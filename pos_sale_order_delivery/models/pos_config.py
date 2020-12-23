# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_ask_warehouse = fields.Boolean(string="Ask Warehouse", default=False)
