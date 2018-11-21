# -*- coding: utf-8 -*-
#  © 2018 Akretion 
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    pos_anonyme_invoice = fields.Boolean()
    session_id = fields.Many2one(
        comodel_name='pos.session', string="PoS Session", readonly=True)

    @api.multi
    def reconcile(
            self, payment_move_ids,
            writeoff_acc_id=False, writeoff_period_id=False,
            writeoff_journal_id=False):
        # TODO check if we can use different period for
        # payment and the writeoff line
        self.ensure_one()
        move_ids = (payment_move_ids | self.move_id.line_id)
        lines2rec = move_ids.browse()
        total = 0.0
        for line in move_ids:
            if line.account_id == self.account_id:
                lines2rec += line
                total += (line.debit or 0.0) - (line.credit or 0.0)

        if not round(total, self.env['decimal.precision'].precision_get(
                'Account')) or writeoff_acc_id:
            lines2rec.reconcile(
                'manual', writeoff_acc_id, writeoff_period_id,
                writeoff_journal_id)
        else:
            code = self.currency_id.symbol
            # TODO: use currency's formatting function
            msg = (_("Invoice partially paid: %s%s of %s%s (%s%s remaining).")
                   % (0, code, self.amount_total, code, total, code))
            self.message_post(body=msg)
            lines2rec.reconcile_partial('manual')

        # Update the stored value (fields.function),
        # so we write to trigger recompute
        return self.write({})

    @api.multi
    def invoice_validate(self):
        # Update invoice partner on sale order and update partner on
        # sale order statement if different on the invoice.
        # In order not to have inconsistency on the partners when the reconcile
        for invoice in self:
            for order in invoice.sale_ids:
                if (invoice.pos_anonyme_invoice and
                    invoice.session_id == order.session_id and
                        order.partner_invoice_id != invoice.partner_id):
                    order.write({'partner_id': invoice.partner_id.id,
                                 'partner_invoice_id': invoice.partner_id.id})
                    order.statement_ids.write(
                        {'partner_id': invoice.partner_id.id})
        return super(AccountInvoice, self).invoice_validate()
