# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _process_order(self, pos_order):
        # remove fake payment
        pos_order["statement_ids"] = [
            statement
            for statement in pos_order["statement_ids"]
            if statement[2]["journal_id"] != -1
        ]
        return super()._process_order(pos_order)
