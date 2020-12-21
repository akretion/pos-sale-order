# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        res["client_order_ref"] = ui_order["client_order_ref"]
        return res
