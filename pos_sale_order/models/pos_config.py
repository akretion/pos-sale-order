# copyright 2020 akretion (https://www.akretion.com).
# @author sébastien beau <sebastien.beau@akretion.com>
# license agpl-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    anonymous_partner_id = fields.Many2one("res.partner", string="Anonymous Partner")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", required=True)
    stock_location_id = fields.Many2one(
        "stock.location",
        string="Stock Location",
        related="warehouse_id.lot_stock_id",
        required=False,
        store=True,
    )
