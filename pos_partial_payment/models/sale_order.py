# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _process_order(self, order, draft, existing_order):
        # remove fake payment
        order["data"]["statement_ids"] = [
            statement
            for statement in order["data"]["statement_ids"]
            if statement[2]["payment_method_id"] != -1
        ]
        return super()._process_order(order, draft, existing_order)
