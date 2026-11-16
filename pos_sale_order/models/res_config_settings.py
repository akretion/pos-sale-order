# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_anonymous_partner_id = fields.Many2one(
        related="pos_config_id.anonymous_partner_id",
        string="Anonymous Partner",
        readonly=False,
    )
