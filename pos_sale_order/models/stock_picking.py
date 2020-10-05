# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def open_pos_delivery_wizard(self):
        self.ensure_one()
        wizard = self.env["pos.delivery.wizard"].create_wizard(self)
        action = wizard.get_formview_action()
        action["target"] = "new"
        return action
