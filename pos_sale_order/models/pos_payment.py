# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    pos_sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="cascade",
        required=True,
        readonly=True,
    )
    payment_method_id = fields.Many2one(readonly=True)
    pos_order_id = fields.Many2one(required=False)
    session_id = fields.Many2one(related=False, readonly=True)
    partner_id = fields.Many2one(related="pos_sale_order_id.partner_id")
    company_id = fields.Many2one(related="pos_sale_order_id.company_id")
    currency_id = fields.Many2one(related="pos_sale_order_id.currency_id")
    currency_rate = fields.Float(related="pos_sale_order_id.currency_rate")
