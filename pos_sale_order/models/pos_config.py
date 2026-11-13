# copyright 2020 akretion (https://www.akretion.com).
# @author sébastien beau <sebastien.beau@akretion.com>
# license agpl-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    anonymous_partner_id = fields.Many2one(
        "res.partner",
        string="Anonymous Partner",
        required=True,
        default=lambda s: s._get_default_partner(),
    )

    def _get_default_partner(self):
        return self.env.ref("pos_sale_order.res_partner_anonymous")
