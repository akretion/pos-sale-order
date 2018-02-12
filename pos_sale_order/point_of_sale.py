# coding: utf-8
# © 2016 toDay Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from openerp import fields, models, api, _
from openerp.exceptions import Warning as UserError
from openerp.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _sql_constraints = [('pos_reference_uniq',
                         'unique (pos_reference, session_id)',
                         'The pos_reference must be uniq per session')]

    pos_reference = fields.Char(string='Receipt Ref',
                                readonly=True,
                                copy=False,
                                default='')
    session_id = fields.Many2one('pos.session', string='Session',
                                 select=1,
                                 domain="[('state', '=', 'opened')]",
                                 states={'draft': [('readonly', False)]},
                                 readonly=True)
    payment_ids = fields.Many2many(readonly=True)
    statement_ids = fields.One2many(
        'account.bank.statement.line',
        'pos_so_statement_id', string='Payments',
        states={'draft': [('readonly', False)]}, readonly=True)

    @api.multi
    def confirm_sale_from_pos(self):
        " Make sale confirmation optional "
        self.ensure_one()
        return True

    @api.model
    def _prepare_invoice(self, order, lines):
        res = super(SaleOrder, self)._prepare_invoice(order, lines)
        pos_anonym_journal = self.env.context.get(
            'pos_anonym_journal', False)
        if pos_anonym_journal:
            res['journal_id'] = pos_anonym_journal.id
        return res


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def _prepare_product_onchange_params(self, order, line):
        return [
            (order['pricelist_id'], line['product_id']),
            {
                'qty': line['product_uom_qty'],
                'uom': False,
                'qty_uos': 0,
                'uos': False,
                'name': '',
                'partner_id': order['partner_id'],
                'lang': False,
                'update_tax': True,
                'date_order': False,
                'packaging': False,
                'fiscal_position': order.get('fiscal_position'),
                'flag': False,
                'warehouse_id': order['warehouse_id']
            }]

    @api.multi
    def _merge_product_onchange(self, order, onchange_vals, line):
        default_key = [
            'name',
            'product_uos_qty',
            'product_uom',
            'th_weight',
            'product_uos']
        for key in default_key:
            line[key] = onchange_vals.get(key)
        if onchange_vals.get('tax_id'):
            line['tax_id'] = [[6, 0, onchange_vals['tax_id']]]

    @api.multi
    def _update_sale_order_line_vals(self, order, line):
        sale_line_obj = self.env['sale.order.line'].browse(False)
        if line.get('qty'):
            line['product_uom_qty'] = line.pop('qty')
        args, kwargs = self._prepare_product_onchange_params(order, line)

        vals = sale_line_obj.product_id_change_with_wh(*args, **kwargs)
        self._merge_product_onchange(order, vals['value'], line)

    @api.multi
    def _prepare_sale_order_vals(self, ui_order):
        pos_session = self.env['pos.session'].browse(
            ui_order['pos_session_id'])
        config = pos_session.config_id
        if not ui_order['partner_id']:
            partner_id = config.anonymous_partner_id.id
            ui_order['partner_id'] = partner_id
        return {
            'pricelist_id': config.pricelist_id.id,
            'warehouse_id': config.warehouse_id.id,
            'section_id': ui_order.get('section_id') or False,
            'user_id': ui_order.get('user_id') or False,
            'session_id': ui_order['pos_session_id'],
            'order_line': ui_order['lines'],
            'pos_reference': ui_order['name'],
            'partner_id': ui_order.get('partner_id') or False,
            'order_policy': 'manual',
        }

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        sale_obj = self.env['sale.order']
        submitted_references = [o['data']['name'] for o in orders]
        existing_orders = sale_obj.search([
            ('pos_reference', 'in', submitted_references),
        ])
        existing_references = existing_orders.mapped('pos_reference')
        orders_to_save = [o for o in orders if (
            o['data']['name'] not in existing_references)]
        order_ids = existing_orders.ids

        prec_acc = self.env['decimal.precision'].precision_get('Account')

        for tmp_order in orders_to_save:
            to_invoice = tmp_order.get('to_invoice', False)
            ui_order = tmp_order['data']

            session = self.env['pos.session'].browse(
                ui_order['pos_session_id'])
            if session.state == 'closing_control' or session.state == 'closed':
                raise UserError(
                    u"La session '%s' du PdV est close.\nVeullez fermer ce "
                    u"dernier et le relancer\nsi vous souhaitez faire "
                    u"une autre vente" % session.name)

            vals = self._prepare_sale_order_vals(ui_order)
            for line in vals['order_line']:
                self._update_sale_order_line_vals(vals, line[2])
            order = sale_obj.create(vals)

            journal_ids = set()

            payments = ui_order.get('statement_ids', []) or []
            for payment in payments:
                if payment:
                    self.add_payment(
                        order.id, self._payment_fields(payment[2]))
                    journal_ids.add(payment[2]['journal_id'])

            if session.sequence_number <= ui_order['sequence_number']:
                session.write(
                    {'sequence_number': ui_order['sequence_number'] + 1})
                session.refresh()

            if payments and not float_is_zero(
                    ui_order['amount_return'], prec_acc):
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    # Select for change one of the cash
                    # journals used in this payment
                    cash_journals = self.env['account.journal'].search([
                        ('type', '=', 'cash'),
                        ('id', 'in', list(journal_ids)),
                    ], limit=1)
                    if not cash_journals:
                        # If none, select for change one of
                        # the cash journals of the POS
                        # This is used for example when
                        # a customer pays by credit card
                        # an amount higher than total amount
                        # of the order and gets cash back
                        cash_journals = [
                            statement.journal_id for statement
                            in session.statement_ids
                            if statement.journal_id.type == 'cash']
                        if not cash_journals:
                            raise UserError(
                                _("No cash statement found for this session."
                                  " Unable to record returned cash."))
                    cash_journal = cash_journals[0]
                self.add_payment(order.id, {
                    'amount': -ui_order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                })

            if order.confirm_sale_from_pos():
                order.signal_workflow('order_confirm')
                if to_invoice:
                    invoice_obj = self.env['account.invoice']
                    order.signal_workflow('manual_invoice')
                    invoice = invoice_obj.browse(order.invoice_ids.ids)
                    invoice.signal_workflow('invoice_open')
                    invoice.write({'sale_ids': [(6, 0, [order.id])]})
                order_ids.append(order.id)

        return order_ids

    @api.multi
    def _prepare_payment_vals(self, order_id, data):
        context = dict(self._context or {})
        property_obj = self.env['ir.property']
        order = self.env['sale.order'].browse(order_id)
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', time.strftime('%Y-%m-%d')),
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': order.partner_id and (
                self.env['res.partner']._find_accounting_partner(
                    order.partner_id).id or False),
        }
        account_def = property_obj.get('property_account_receivable',
                                       'res.partner')
        args['account_id'] = ((
            order.partner_id and
            order.partner_id.property_account_receivable and
            order.partner_id.property_account_receivable.id) or
            (account_def and account_def.id) or False)

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined '
                        'to make payment.')
            else:
                msg = _('There is no receivable account defined '
                        'to make payment for the partner: "%s" (id:%d).') % (
                            order.partner_id.name, order.partner_id.id,)
            raise UserError(_('Configuration Error!'), msg)

        context.pop('pos_session_id', False)

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        if not(journal_id or statement_id):
            raise UserError(
                "No statement_id or journal_id passed to the method!")

        for statement in order.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.statement_id.id
                break

        if not statement_id:
            raise UserError(_('Error!'),
                            _('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'journal_id': journal_id,
            'pos_so_statement_id': order_id,
            'ref': order.session_id.name,
            'sale_ids': [(6, 0, [order_id])]
        })

        return args

    @api.multi
    def add_payment(self, order_id, data):
        """Create a new payment for the order"""
        statement_line_obj = self.env['account.bank.statement.line']
        args = self._prepare_payment_vals(order_id, data)
        return statement_line_obj.create(args)


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def _get_so_domains(
            self, vals, anonym_partner_id, anonym_order=True):
        self.ensure_one()
        vals = [
            ('session_id', '=', self.id),
            ('state', '=', 'manual'),
        ]
        if anonym_order:
            vals.append(('partner_id', '=', anonym_partner_id),)
        else:
            vals.append(('partner_id', '!=', anonym_partner_id),)
        return vals

    @api.multi
    def _confirm_orders(self):
        for session in self:
            partner_id = session.config_id.anonymous_partner_id.id
            invoices = self.env['account.invoice'].browse(False)
            # invoiced order : get generated invoice
            # and reconcile it with pos payment
            generated_invoices = self._get_generated_invoice()
            generated_invoices.signal_workflow('invoice_open')

            self._reconcile_invoice_with_pos_payment(generated_invoices)
            invoices |= generated_invoices
            # anonym orders : generate grouped invoice for anonym patner
            # and reconcile it with pos payment
            grouped_anonym_invoice = self._generate_invoice(
                partner_id=partner_id,
                grouped=True, anonym_order=True, anonym_journal=True)
            self._reconcile_invoice_with_pos_payment(grouped_anonym_invoice)
            invoices |= grouped_anonym_invoice
            # not anonym orders : generate invoices for not anonym patner
            # and reconcile their with pos payment
            invoice_not_anonym = self._generate_invoice(
                partner_id=partner_id,
                grouped=True, anonym_order=False, anonym_journal=True)
            self._reconcile_invoice_with_pos_payment(invoice_not_anonym)
            invoices |= invoice_not_anonym
            return invoices
        return True

    def _get_generated_invoice(self):
        sale_obj = self.env['sale.order']
        domains = [
            ('session_id', '=', self.id),
        ]
        orders = sale_obj.search(domains)
        invoices = self.env['account.invoice'].browse(False)

        for order in orders:
            if order.invoice_ids:
                invoices |= order.invoice_ids
        return invoices

    def _generate_invoice(
            self, partner_id=False, grouped=False,
            anonym_order=True, anonym_journal=True):
        sale_obj = self.env['sale.order']
        domains = {}
        domains = self._get_so_domains(
            domains, partner_id, anonym_order=anonym_order)
        orders = sale_obj.search(domains)
        orders = orders.filtered(lambda so: not so.invoice_exists)
        pos_anonym_journal = False
        if anonym_journal:
            pos_anonym_journal = self.config_id.journal_id
        invoice_id = orders.with_context(
            pos_anonym_journal=pos_anonym_journal
        ).action_invoice_create(grouped=grouped)
        invoice = self.env['account.invoice'].browse(invoice_id)
        if anonym_order:
            invoice.write({'pos_anonyme_invoice': True})
        orders.signal_workflow('manual_invoice')
        invoice.signal_workflow('invoice_open')
        invoice.write({'sale_ids': [(6, 0, orders.ids)]})
        return invoice

    def _reconcile_invoice_with_pos_payment(
            self, invoices):
        if not invoices:
            return False
        for invoice in invoices:
            if invoice.state == 'open':
                payment_move_ids = self.env['account.move.line'].browse(False)
                for order in invoice.sale_ids:
                    for statement in order.statement_ids:
                        payment_move_ids |= statement.journal_entry_id.line_id
                if payment_move_ids:
                    invoice.reconcile(payment_move_ids)
        return True


class PosConfig(models.Model):
    _inherit = 'pos.config'

    anonymous_partner_id = fields.Many2one(
        'res.partner',
        string='Anonymous Partner')
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True)
    stock_location_id = fields.Many2one(
        'stock.location',
        string='Stock Location',
        related='warehouse_id.lot_stock_id',
        readonly=True,
        required=False)
