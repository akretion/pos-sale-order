# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pos_order_id = fields.Many2one(
        "pos.order",
        store=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("pos_order_id"):
                # Link sol to so through pos_order_id
                vals["order_id"] = (
                    self.env["pos.order"].browse(vals["pos_order_id"]).sale_order_id.id
                )
        return super().create(vals_list)
