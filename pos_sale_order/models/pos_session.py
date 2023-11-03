# copyright 2020 akretion (https://www.akretion.com).
# @author sébastien beau <sebastien.beau@akretion.com>
# license agpl-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from odoo.addons.point_of_sale.models.pos_session import PosSession


# TODO V16 we should add a hook in odoo native
# Monkey patch native action_pos_session_closing_control
# to allow draft order
def action_pos_session_closing_control(self):
    self._check_pos_session_balance()
    for session in self:
        # if any(order.state == 'draft' for order in session.order_ids):
        #    raise UserError(_("You cannot close the POS when orders are still in draft"))
        if session.state == "closed":
            raise UserError(_("This session is already closed."))
        session.write({"state": "closing_control", "stop_at": fields.Datetime.now()})
        if not session.config_id.cash_control:
            session.action_pos_session_close()


PosSession.action_pos_session_closing_control = action_pos_session_closing_control


class PosSession(models.Model):
    _inherit = "pos.session"

    order_ids = fields.One2many("sale.order", "session_id", string="Orders")
    invoice_ids = fields.One2many("account.move", "session_id", string="Invoices")
    payment_ids = fields.One2many("pos.payment", "session_id", string="Payments")

    def _compute_order_count(self):
        orders_data = self.env["sale.order"].read_group(
            [("session_id", "in", self.ids)], ["session_id"], ["session_id"]
        )
        sessions_data = {
            order_data["session_id"][0]: order_data["session_id_count"]
            for order_data in orders_data
        }
        for session in self:
            session.order_count = sessions_data.get(session.id, 0)

    def action_view_order(self):
        return {
            "name": _("Orders"),
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "views": [
                (self.env.ref("sale.view_order_tree").id, "tree"),
                (self.env.ref("sale.view_order_form").id, "form"),
            ],
            "type": "ir.actions.act_window",
            "domain": [("session_id", "in", self.ids)],
        }

    def _prepare_sale_statement(self, payments, record_ref):
        # Payment can be group by sale order or per invoice
        # in case that their are grouped by sale order the payment ref
        # should be the sale order ref + the invoice ref
        # In case that their are grouped by invoice the payment ref
        # should be the invoice ref
        ref = None
        if record_ref._name == "sale.order":
            ref = " - ".join([record_ref.name] + record_ref.invoice_ids.mapped("name"))
        elif record_ref._name == "account.move":
            ref = " - ".join(record_ref.mapped("name"))
        method = payments.payment_method_id
        return {
            "date": fields.Date.context_today(self),
            "amount": sum(payments.mapped("amount")),
            "payment_ref": self.name,
            "ref": ref,
            "journal_id": method.cash_journal_id.id,
            "counterpart_account_id": method.receivable_account_id.id,
            "partner_id": payments.partner_id.id,
        }

    def _get_receivable_line(self, payments):
        # Ensure that everything is invoiced
        sale_missing_invoice = payments.pos_sale_order_id.filtered(
            lambda s: not s.invoice_ids.filtered(lambda s: s.state == "posted")
        )
        if sale_missing_invoice:
            raise UserError(
                _("Following sales are not invoiced, please invoice it: \n- %s")
                % ("\n- ".join(sale_missing_invoice.mapped("name")))
            )
        return payments.pos_sale_order_id.invoice_ids.filtered(
            # skip canceled invoice
            lambda s: s.state
            == "posted"
        ).line_ids.filtered(
            # get receivable line
            lambda s: s.account_id
            == payments.payment_method_id.receivable_account_id
        )

    def _create_bank_statement_line(self, statement, payments, record_ref):
        vals = self._prepare_sale_statement(payments, record_ref)
        vals["statement_id"] = statement.id
        bk_line = self.env["account.bank.statement.line"].create(vals)
        return bk_line.line_ids.filtered(
            lambda s: s.account_id == payments.payment_method_id.receivable_account_id
        )

    def _create_bank_statement_line_and_reconcile(self):
        self.ensure_one()
        payments = self.env["pos.payment"].search([("session_id", "=", self.id)])
        grouped_payments = defaultdict(
            lambda: defaultdict(lambda: self.env["pos.payment"])
        )
        # Depending of the configuration we split the payment per sale order
        # or by invoice
        # Grouping by invoice make it easier to reconcile and to understand what
        # have been reconciled with
        for payment in payments:
            if payment.payment_method_id.split_transactions:
                key = payment.pos_sale_order_id
            else:
                key = payment.pos_sale_order_id.invoice_ids
            grouped_payments[payment.payment_method_id][key] |= payment

        inv2payment = defaultdict(lambda: self.env["account.move.line"])

        for method, payment_per_key in grouped_payments.items():
            statement = self.statement_ids.filtered(
                lambda s: s.journal_id == method.cash_journal_id
            )
            if not statement and method.cash_journal_id:
                statement = self.env["account.bank.statement"].create(
                    {
                        "journal_id": method.cash_journal_id.id,
                        "pos_session_id": self.id,
                        "user_id": self.env.user.id,
                        "name": self.name,
                    }
                )
            for record_ref, payments in payment_per_key.items():
                if not float_is_zero(
                    sum(payments.mapped("amount")),
                    precision_rounding=statement.currency_id.rounding,
                ):
                    inv_receivable_line = self._get_receivable_line(payments)
                    payment_receivable_line = self._create_bank_statement_line(
                        statement, payments, record_ref
                    )
                    inv2payment[inv_receivable_line] |= payment_receivable_line

        self.statement_ids.button_post()
        self.statement_ids.button_validate()

        # Ensure that nothing is already reconciled, and do it
        for inv_line, pay_line in inv2payment.items():
            lines = inv_line | pay_line
            for reconciled in lines.filtered("reconciled"):
                if reconciled.debit == 0 and reconciled.credit == 0:
                    continue
                elif reconciled.move_id.move_type == "out_invoice":
                    message = _("The invoice %s is already paid, please remove it")
                else:
                    message = _("The move %s is already reconciled")
                raise UserError(message % ", ".join(reconciled.mapped("name")))
            lines.reconcile()

    def _create_account_move(self):
        self.ensure_one()
        # we create all invoice so odoo code will not generate account move for order
        orders = self._get_order_to_confirm()
        orders.action_confirm()
        self._check_no_draft_invoice()

        partner_to_orders = defaultdict(lambda: self.env["sale.order"].browse(False))
        for order in self._get_order_to_invoice():
            partner_to_orders[order.partner_id] += order

        for partner, orders in partner_to_orders.items():
            if partner == self.config_id.anonymous_partner_id:
                orders = orders.with_context(
                    default_journal_id=self.config_id.journal_id.id
                )
            orders._create_invoices(final=True)
            orders.invoice_ids.filtered(lambda s: s.state == "draft").action_post()
        self._create_bank_statement_line_and_reconcile()
        return True

    def _get_order_to_confirm(self):
        return self.order_ids.filtered(lambda s: s.state == "draft")

    def _get_order_to_invoice(self):
        return self.order_ids.filtered(
            lambda s: any(s.mapped("order_line.qty_to_invoice"))
        )

    def _check_no_draft_invoice(self):
        draft_invoices = self.mapped("order_ids.invoice_ids").filtered(
            lambda s: s.state == "draft"
        )
        if draft_invoices:
            orders_name = ", ".join(
                draft_invoices.mapped("line_ids.sale_line_ids.order_id.name")
            )
            raise UserError(
                _("Following order have a draft invoice, please fix it %s")
                % orders_name
            )

    def _check_if_no_draft_orders(self):
        # we can have quotation
        return True

    def _create_picking_at_end_of_session(self):
        return True

    def _validate_session(self):
        super()._validate_session()
        return {
            "type": "ir.actions.client",
            "name": "Point of Sale",
            "tag": "reload",
            "params": {
                "menu_id": self.env.ref("pos_sale_order.menu_pos_sale_order_root").id
            },
        }

    @api.depends("payment_ids.amount")
    def _compute_total_payments_amount(self):
        for session in self:
            session.total_payments_amount = sum(session.mapped("payment_ids.amount"))
