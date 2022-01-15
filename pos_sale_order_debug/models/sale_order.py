# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _build_pos_error_message(self, failed, result):
        for order, _exception in failed:
            error = self.env["pos.sale.error"].sudo()._log_error(order, _exception)
            if error.state != "pending":
                # The Error have been managed so we can skip it
                result["uuids"].append(order["id"])
        return super()._build_pos_error_message(failed, result)
