# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _confirm_pos_order(self, order):
        if order["data"].get("is_quotation"):
            return
        else:
            return super()._confirm_pos_order(order)
