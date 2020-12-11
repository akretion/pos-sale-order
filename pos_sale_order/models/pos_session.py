# copyright 2020 akretion (https://www.akretion.com).
# @author sébastien beau <sebastien.beau@akretion.com>
# license agpl-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = "pos.session"

    order_ids = fields.One2many("sale.order", "session_id", string="Orders")
    invoice_ids = fields.One2many("account.invoice", "session_id", string="Invoices")

    def _confirm_orders(self):
        for session in self:
            draft_sales = session.order_ids.filtered(lambda s: s.state == "draft")
            if draft_sales:
                draft_sales.action_confirm()

            invoices = session.mapped("order_ids.invoice_ids")
            draft_invoices = invoices.filtered(lambda s: s.state == "draft")
            if draft_invoices:
                orders_name = ", ".join(
                    draft_invoices.mapped("invoice_line.sale_line_ids.order_id.name")
                )
                raise UserError(
                    _("Following order have a draft invoice, please fix it %s"),
                    orders_name,
                )

            invoices |= self._generate_invoice(anonymous=True)
            invoices |= self._generate_invoice()
            invoices._reconcile_with_pos_payment()
        self._reconcile_manual_payment()

    def _reconcile_manual_payment(self):
        "Search all invoice not paid linked to statement line and reconcile them"
        for session in self:
            invoices = session.mapped(
                "statement_ids.line_ids.pos_sale_order_id.invoice_ids"
            )
            open_invoices = invoices.filtered(lambda s: s.state == "open")
            open_invoices._reconcile_with_pos_payment()

    def _get_so_domain(self, anonymous=False):
        partner = self.config_id.anonymous_partner_id
        domain = [("session_id", "=", self.id), ("invoice_status", "=", "to invoice")]
        if anonymous:
            domain.append(("partner_id", "=", partner.id))
        else:
            domain.append(("partner_id", "!=", partner.id))
        return domain

    def _generate_invoice(self, anonymous=False):
        if anonymous:
            self = self.with_context(
                default_journal_id=self.config_id.journal_id,
                default_pos_anonyme_invoice=True,
            )
        domain = self._get_so_domain(anonymous=anonymous)
        sales = self.env["sale.order"].search(domain)
        if sales:
            invoice_ids = sales.action_invoice_create()
            invoices = self.env["account.invoice"].browse(invoice_ids)
            invoices.action_invoice_open()
            return invoices
        else:
            return self.env["account.invoice"].browse()
