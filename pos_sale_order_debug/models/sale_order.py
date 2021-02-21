# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _build_pos_error_message(self, failed):
        for order in failed:
            self.env["pos.sale.error"].sudo()._log_error(order)
        return super()._build_pos_error_message(failed)
