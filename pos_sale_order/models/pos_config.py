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
    iface_print_auto = fields.Boolean(compute="_compute_print_option")
    iface_print_via_proxy = fields.Boolean(compute="_compute_print_option")
    iface_print_skip_screen = fields.Boolean(compute="_compute_print_option")

    def _compute_print_option(self):
        for record in self:
            record.iface_print_auto = True
            record.iface_print_via_proxy = True
            record.iface_print_skip_screen = True
