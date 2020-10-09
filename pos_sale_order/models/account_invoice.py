#  © 2018 Akretion
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    pos_anonyme_invoice = fields.Boolean()
    session_id = fields.Many2one(
        comodel_name="pos.session", string="PoS Session", readonly=True
    )

    def _reconcile_with_pos_payment(self):
        for record in self:
            if record.state == "open":
                statement_lines = record.mapped(
                    "invoice_line_ids.sale_line_ids.order_id.statement_ids"
                )
                payment_lines = statement_lines.mapped("journal_entry_ids").filtered(
                    lambda s: s.account_id == record.account_id and not s.reconciled
                )
                if payment_lines:
                    lines = record.move_id.line_ids.filtered(
                        lambda s: s.account_id == record.account_id
                    )
                    lines |= payment_lines
                    lines.reconcile()
        return True

    def _sync_partner_invoice_on_sale(self):
        for record in self:
            if record.session_id:
                orders = record.mapped(
                    "invoice_line_ids.sale_line_ids.order_id"
                ).filtered(lambda s: s.partner_invoice_id != record.partner_id)
                orders.write({"partner_invoice_id": record.partner_id.id})

    def write(self, vals):
        super().write(vals)
        if "partner_id" in vals:
            self._sync_partner_invoice_on_sale()
        return True
