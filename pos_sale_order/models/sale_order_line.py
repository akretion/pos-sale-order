# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PosOrderLineLot(models.Model):
    _inherit = "pos.pack.operation.lot"
    pos_order_line_id = fields.Many2one("sale.order.line")
    order_id = fields.Many2one(
        "sale.order", related="pos_order_line_id.order_id", readonly=False
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pack_lot_ids = fields.One2many(
        "pos.pack.operation.lot", "pos_order_line_id", string="Lot/serial Number"
    )
    custom_attribute_value_ids = fields.One2many(
        related="product_custom_attribute_value_ids"
    )
    session_id = fields.Many2one(related="order_id.session_id")
    refund_orderline_ids = fields.One2many(
        "sale.order.line",
        "refunded_orderline_id",
        "Refund Order Lines",
        help="Orderlines in this field are the lines that refunded this orderline.",
    )
    refunded_orderline_id = fields.Many2one(
        "sale.order.line",
        "Refunded Order Line",
        help="If this orderline is a refund, then the refunded orderline is specified in this field.",
    )
    price_subtotal_incl = fields.Monetary(related="price_total")

    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        "Self",
    )
    qty = fields.Float(related="product_uom_qty")

    def _prepare_tax_base_line_values(self):
        return [line._prepare_base_line_for_taxes_computation() for line in self]

    def _load_pos_data_fields(self, config_id):
        return self.env["pos.order"].__class__._load_pos_data_fields(self, config_id)

    def _load_pos_data_domain(self, data):
        return self.env["pos.order"].__class__._load_pos_data_domain(self, data)

    def _load_pos_data(self, data):
        return self.env["pos.order"].__class__._load_pos_data(self, data)

    @api.depends("order_id.session_id")
    def _get_to_invoice_qty(self):
        for record in self:
            if record.order_id.session_id:
                record.qty_to_invoice = record.product_uom_qty - record.qty_invoiced
            else:
                super(SaleOrderLine, record)._get_to_invoice_qty()
