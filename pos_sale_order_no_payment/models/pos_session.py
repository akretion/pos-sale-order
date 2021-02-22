# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_order_to_confirm(self):
        orders = super()._get_order_to_confirm()
        return orders.filtered(lambda s: not s.is_pos_quotation)

    def _get_order_to_invoice(self):
        orders = super()._get_order_to_invoice()
        return orders.filtered(lambda s: not s.is_pos_quotation)
