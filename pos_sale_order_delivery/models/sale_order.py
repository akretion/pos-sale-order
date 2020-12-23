# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def compute_pos_requested_date(self):
        return {
            "date": "2020-06-20",
            "allowDeliveryNow": True,
        }

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        res["commitment_date"] = ui_order["commitment_date"]
        # TODO: do something with ui_order['deliver_now']
        return res
