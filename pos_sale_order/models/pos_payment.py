# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    pos_sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="cascade",
        readonly=True,
        index=True,
    )
    payment_method_id = fields.Many2one(readonly=True)
    pos_order_id = fields.Many2one(required=False)
    session_id = fields.Many2one(related="pos_sale_order_id.session_id", readonly=True)
    partner_id = fields.Many2one(
        related="pos_sale_order_id.partner_invoice_id.commercial_partner_id"
    )
    company_id = fields.Many2one(related="pos_sale_order_id.company_id")
    currency_id = fields.Many2one(related="pos_sale_order_id.currency_id")
    currency_rate = fields.Float(related="pos_sale_order_id.currency_rate")

    @api.constrains("amount")
    def _check_amount(self):
        for payment in self:
            if payment.pos_sale_order_id.state in ["done"]:
                raise ValidationError(
                    _("You cannot edit a payment for a posted order.")
                )

    def _adapt_vals_to_payment(self, vals, mode):
        vals["pos_sale_order_id"] = vals.pop("pos_order_id")
        return vals
