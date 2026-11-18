# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def _load_pos_data_relations(self, model, response):
        super()._load_pos_data_relations(model, response)
        if model == "pos.order":
            # Force compute to False otherwise the frontend will not send the data
            response["pos.order"]["relations"]["partner_id"]["compute"] = False
            response["pos.order"]["relations"]["partner_id"]["related"] = False
        if model == "pos.order.line":
            # Force compute to False otherwise the frontend will not send the data
            response["pos.order.line"]["relations"]["product_id"]["compute"] = False
            response["pos.order.line"]["relations"]["product_id"]["related"] = False
            response["pos.order.line"]["relations"]["qty"]["compute"] = False
            response["pos.order.line"]["relations"]["qty"]["related"] = False
            response["pos.order.line"]["relations"]["price_unit"]["compute"] = False
            response["pos.order.line"]["relations"]["price_unit"]["related"] = False


class PosOrder(models.Model):
    _inherit = "pos.order"
    _inherits = {
        "sale.order": "sale_order_id",
    }

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        inherited=True,
        related="sale_order_id.partner_id",
        readonly=False,
    )


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"
    _inherits = {
        "sale.order.line": "sale_order_line_id",
    }

    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
        required=True,
        ondelete="cascade",
    )
    name = fields.Text(
        inherited=True,
        related="sale_order_line_id.name",
        readonly=False,
    )
    product_id = fields.Many2one(
        inherited=True,
        related="sale_order_line_id.product_id",
        readonly=False,
    )
    qty = fields.Float(
        related="sale_order_line_id.product_uom_qty",
        readonly=False,
    )
    price_unit = fields.Float(
        inherited=True,
        related="sale_order_line_id.price_unit",
        readonly=False,
    )
    pos_order_id = fields.Many2one(
        inherited=True,
        related="sale_order_line_id.pos_order_id",
        readonly=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Forward pos order_id to sale.order inherited pos_order_id
        for vals in vals_list:
            vals["pos_order_id"] = vals.get("order_id")
        return super().create(vals_list)
