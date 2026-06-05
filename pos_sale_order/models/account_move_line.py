# Copyright 2024 Akretion (https://www.akretion.com).
# @author Matthieu SAISON <matthieu.saison@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pos_session_id = fields.Many2one(
        "pos.session", related="move_id.session_id", store=True
    )
    pos_config_id = fields.Many2one(
        "pos.config", related="move_id.session_id.config_id", store=True
    )
