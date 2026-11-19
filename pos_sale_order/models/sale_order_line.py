# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_refund_data(self, refund_order):
        self.ensure_one()
        return {
            "name": self.name + _(" REFUND"),
            "product_uom_qty": -self.product_uom_qty,
            "price_unit": self.price_unit,
            "order_id": refund_order.id,
        }
