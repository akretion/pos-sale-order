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
    _name = "sale.order.line"
    _inherit = ("sale.order.line", "pos.load.mixin")

    pack_lot_ids = fields.One2many(
        "pos.pack.operation.lot", "pos_order_line_id", string="Lot/serial Number"
    )
    attribute_value_ids = fields.Many2many(
        related="product_no_variant_attribute_value_ids"
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
    refunded_qty = fields.Float(
        "Refunded Quantity",
        compute="_compute_refund_qty",
        help="Number of items refunded in this orderline.",
    )
    uuid = fields.Char(string="Uuid", readonly=True, copy=False)
    price_subtotal_incl = fields.Monetary(related="price_total")

    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        compute="_compute_sale_order_line_id",
        search="_search_sale_order_line_id",
    )
    pos_order_line_ids = fields.One2many("sale.order.line", "sale_order_line_id")

    qty = fields.Float(related="product_uom_qty")
    tax_ids = fields.Many2many(related="tax_id")
    combo_parent_id = fields.Many2one(
        "sale.order.line",
        string="Combo Parent",
    )
    combo_line_ids = fields.One2many(
        "sale.order.line",
        "combo_parent_id",
        string="Combo Lines",
    )

    def _prepare_tax_base_line_values(self):
        return [line._prepare_base_line_for_taxes_computation() for line in self]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            "qty",
            "attribute_value_ids",
            "custom_attribute_value_ids",
            "price_unit",
            # "skip_change",
            "uuid",
            "price_subtotal",
            "price_subtotal_incl",
            "order_id",
            # "note",
            # "price_type",
            "write_date",
            "product_id",
            "discount",
            "tax_ids",
            "pack_lot_ids",
            # "customer_note",
            "refunded_qty",
            # "price_extra",
            # "full_product_name",
            "refunded_orderline_id",
            "combo_parent_id",
            "combo_line_ids",
            "combo_item_id",
            "refund_orderline_ids",
            "discount",
            "display_name",
            "price_total",
            "price_unit",
            "product_id",
            "product_uom_qty",
            "qty_delivered",
            "qty_invoiced",
            "qty_to_invoice",
            "display_type",
            "name",
            "tax_id",
            "is_downpayment",
            "write_date",
            "product_no_variant_attribute_value_ids",
            "product_custom_attribute_value_ids",
            # "sale_order_origin_id",
            "sale_order_line_id",
            # "down_payment_details",
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        return self.env["pos.order.line"].__class__._load_pos_data_domain(self, data)

    @api.depends("refund_orderline_ids", "refund_orderline_ids.order_id.state")
    def _compute_refund_qty(self):
        return self.env["pos.order.line"].__class__._compute_refund_qty(self)

    def _compute_sale_order_line_id(self):
        for line in self:
            line.sale_order_line_id = line

    def _search_sale_order_line_id(self, operator, value):
        return [("id", operator, value)]

    @api.depends("order_id.session_id")
    def _get_to_invoice_qty(self):
        for record in self:
            if record.order_id.session_id:
                record.qty_to_invoice = record.product_uom_qty - record.qty_invoiced
            else:
                super(SaleOrderLine, record)._get_to_invoice_qty()
