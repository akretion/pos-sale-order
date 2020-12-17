# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    pos_sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order", ondelete="cascade"
    )
