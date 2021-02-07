# copyright 2020 akretion (https://www.akretion.com).
# @author sébastien beau <sebastien.beau@akretion.com>
# license agpl-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, fields, models
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = "pos.session"

    order_ids = fields.One2many("sale.order", "session_id", string="Orders")
    invoice_ids = fields.One2many("account.move", "session_id", string="Invoices")

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

    def _prepare_sale_statement(self, partner, method, payments):
        return {
            "date": fields.Date.context_today(self),
            "amount": sum(payments.mapped("amount")),
            "payment_ref": self.name,
            "journal_id": method.cash_journal_id.id,
            "counterpart_account_id": method.receivable_account_id.id,
            "partner_id": partner.id,
        }

    def _create_bank_statement_line_and_reconcile(self):
        to_reconcile = []
        self.ensure_one()
        payments = self.env["pos.payment"].search([("session_id", "=", self.id)])
        grouped_payments = defaultdict(
            lambda: defaultdict(lambda: self.env["pos.payment"])
        )
        for payment in payments:
            grouped_payments[payment.payment_method_id][payment.partner_id] |= payment

        for method, payment_per_partner in grouped_payments.items():
            statement = self.statement_ids.filtered(
                lambda s: s.journal_id == method.cash_journal_id
            )
            for partner, payments in payment_per_partner.items():
                vals = self._prepare_sale_statement(partner, method, payments)
                vals["statement_id"] = statement.id
                bk_line = self.env["account.bank.statement.line"].create(vals)
                move_lines = (
                    bk_line.move_id.line_ids
                    + payments.pos_sale_order_id.invoice_ids.line_ids
                )
                lines = move_lines.filtered(
                    lambda s: s.account_id == method.receivable_account_id
                )
                to_reconcile.append(lines)
        self.statement_ids.button_post()
        for lines in to_reconcile:
            lines.reconcile()

    def _create_account_move(self):
        self.ensure_one()
        # we create all invoice so odoo code will not generate account move for order
        orders = self._get_order_to_confirm()
        orders.action_confirm()
        self._check_no_draft_invoice()

        # TODO
        # - check journal used
        for partner, orders in self._get_order_to_invoice().items():
            if partner == self.config_id.anonymous_partner_id:
                orders = orders.with_context(
                    default_journal_id=self.config_id.journal_id
                )
            orders._create_invoices()
            orders.invoice_ids.action_post()
        # TODO create payment for cash and check
        self._create_bank_statement_line_and_reconcile()
        return True

    def _get_order_to_confirm(self):
        return self.order_ids.filtered(lambda s: s.state == "draft")

    def _get_order_to_invoice(self):
        partner_to_orders = defaultdict(lambda: self.env["sale.order"].browse(False))
        for order in self.order_ids:
            if any(order.mapped("order_line.qty_to_invoice")):
                partner_to_orders[order.partner_id.id] += order
        return partner_to_orders

    def _check_no_draft_invoice(self):
        draft_invoices = self.mapped("order_ids.invoice_ids").filtered(
            lambda s: s.state == "draft"
        )
        if draft_invoices:
            orders_name = ", ".join(
                draft_invoices.mapped("move_line.sale_line_ids.order_id.name")
            )
            raise UserError(
                _("Following order have a draft invoice, please fix it %s"),
                orders_name,
            )

    def _check_if_no_draft_orders(self):
        # we can have quotation
        return True

    def _create_picking_at_end_of_session(self):
        return True
