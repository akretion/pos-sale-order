# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


def nosearch(*args, **kwargs):
    return [("id", "=", 0)]


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ("sale.order.line", "pos.load.mixin")

    # Interesting fields
    uuid = fields.Char(string="Uuid", readonly=True, copy=False)
    full_product_name = fields.Char()

    # Related fields
    session_id = fields.Many2one(related="order_id.session_id")

    # Mapped Fields
    qty = fields.Float(related="product_uom_qty", readonly=False)
    tax_ids = fields.Many2many(related="tax_id")
    price_subtotal_incl = fields.Monetary(related="price_total")
    attribute_value_ids = fields.Many2many(
        related="product_no_variant_attribute_value_ids"
    )
    custom_attribute_value_ids = fields.One2many(
        related="product_custom_attribute_value_ids"
    )

    # Discarded fields
    price_type = fields.Selection(
        [
            ("original", "Original"),
            ("manual", "Manual"),
            ("automatic", "Automatic"),
        ],
        default="original",
        store=False,
    )
    price_extra = fields.Float(store=False)
    skip_change = fields.Boolean(store=False)
    note = fields.Char(store=False)
    customer_note = fields.Char(store=False)
    down_payment_details = fields.Text(store=False)
    sale_order_line_id = fields.Many2one("sale.order.line", store=False)
    sale_order_origin_id = fields.Many2one("sale.order", store=False)
    pos_order_line_ids = fields.One2many(
        "sale.order.line",
        store=False,
        search=nosearch,
    )
    combo_parent_id = fields.Many2one("sale.order.line", store=False)
    combo_line_ids = fields.One2many("sale.order.line", store=False)
    is_edited = fields.Boolean(store=False)
    is_total_cost_computed = fields.Boolean(store=False)
    total_cost = fields.Float(store=False)
    margin = fields.Monetary(store=False)
    margin_percent = fields.Float(store=False, digits=(12, 4))
    tax_ids_after_fiscal_position = fields.Many2many("account.tax", store=False)
    notice = fields.Char(store=False)
    refund_orderline_ids = fields.One2many(
        "sale.order.line",
        store=False,
        search=nosearch,
    )
    refunded_orderline_id = fields.Many2one("sale.order.line", store=False)
    pack_lot_ids = fields.One2many("pos.pack.operation.lot", store=False)
    refunded_qty = fields.Float("Refunded Quantity", store=False)

    def _prepare_tax_base_line_values(self):
        return [line._prepare_base_line_for_taxes_computation() for line in self]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return self.env["pos.order.line"]._load_pos_data_fields(config_id)

    @api.model
    def _load_pos_data_domain(self, data):
        return self.env["pos.order.line"]._load_pos_data_domain(data)

    @api.depends("order_id.session_id")
    def _get_to_invoice_qty(self):
        for record in self:
            if record.order_id.session_id:
                record.qty_to_invoice = record.product_uom_qty - record.qty_invoiced
            else:
                super(SaleOrderLine, record)._get_to_invoice_qty()
