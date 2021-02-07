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
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        required=True,
        default=lambda s: s._get_default_warehouse(),
    )
    picking_type_id = fields.Many2one(
        related="warehouse_id.out_type_id",
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

    def _get_default_warehouse(self):
        return self.env["stock.warehouse"].search(
            [
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

    def _get_default_partner(self):
        return self.env.ref("pos_sale_order.res_partner_anonymous")
