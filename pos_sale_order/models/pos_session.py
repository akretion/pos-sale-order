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

    def _create_account_move(self):
        self.ensure_one()
        # we create all invoice so odoo code will not generate account move for order
        # TODO FIX quotation case (we should have a pos_type)
        orders = self._get_order_to_confirm()
        orders.action_confirm()
        self._check_no_draft_invoice()

        # TODO
        # - check case where we have draft order
        # - check journal used
        # - activate mismatch partner
        for partner, orders in self._get_order_to_invoice().items():
            if partner == self.config_id.anonymous_partner_id:
                orders = orders.with_context(
                    default_journal_id=self.config_id.journal_id
                )
            orders._create_invoices()
            orders.invoice_ids.action_post()
        return super()._create_account_move()

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
