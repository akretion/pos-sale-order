# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pos_auto_delivery = fields.Boolean(
        help="Technical Field to flag order that should be delivered automatically"
    )

    @api.model
    def _get_product_ids(self, data):
        product_ids = []
        for _a, _b, line in data["lines"]:
            product_ids.append(line["product_id"])

            # compatibility with pos_sale_configurator_option
            # simple if to avoid glue module
            if line.get("config", {}).get("selected_options"):
                for option in line["config"]["selected_options"]:
                    product_ids.append(option["product_id"])

        return product_ids

    @api.model
    def compute_pos_requested_date(self, data):
        product_ids = self._get_product_ids(data)
        products = self.env["product.product"].browse(product_ids)
        sale_delay = max(products.mapped("sale_delay"))
        allow_delivery_now = all(products.mapped("pos_delivery_now_allowed"))
        allow_delivery_later = True
        no_delivery_message = False
        return {
            "date": str(date.today() + timedelta(days=sale_delay)),
            "allow_delivery_now": allow_delivery_now,
            "allow_delivery_later": allow_delivery_later,
            "no_delivery_message": no_delivery_message,
        }

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        res.update(
            {
                "commitment_date": ui_order["commitment_date"],
                "pos_auto_delivery": ui_order["deliver_now"],
            }
        )
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for record in self:
            if record.pos_auto_delivery:
                record.with_delay().action_deliver_all()
        return res

    def action_deliver_all(self):
        for picking in self.picking_ids:
            for line in picking.move_lines:
                line.quantity_done = line.product_uom_qty
            picking.button_validate()
