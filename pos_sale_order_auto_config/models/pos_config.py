# Copyright 2023 Akretion (https://www.akretion.com).
# @author Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_print_pause = fields.Boolean("Faire des pauses entre les impressions ?")
    iface_cashdrawer = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_electronic_scale = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_vkeyboard = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_customer_facing_display = fields.Boolean(
        compute="_compute_pos_config", store=True
    )
    iface_print_via_proxy = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_scan_via_proxy = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_big_scrollbars = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_print_auto = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_print_skip_screen = fields.Boolean(compute="_compute_pos_config", store=True)
    iface_tax_included = fields.Selection(compute="_compute_pos_config", store=True)
    iface_display_categ_images = fields.Boolean(
        compute="_compute_pos_config", store=True
    )
    proxy_ip = fields.Char(compute="_compute_pos_config", store=True)
    iface_tipproduct = fields.Boolean(compute="_compute_pos_config", store=True)
    use_pricelist = fields.Boolean(compute="_compute_pos_config", store=True)
    is_posbox = fields.Boolean(compute="_compute_pos_config", store=True)
    anonymous_partner_id = fields.Many2one(
        "res.partner",
        string="Anonymous Partner",
        compute="_compute_pos_config",
        store=True,
    )
    cash_control = fields.Boolean(default=True)
    iface_ask_warehouse = fields.Boolean()

    @api.depends("name", "active")
    def _compute_pos_config(self):
        anonymous_partner = self.env.ref("pos_sale_order.res_partner_anonymous")
        for record in self:
            record.iface_cashdrawer = True
            record.iface_electronic_scale = False
            record.iface_vkeyboard = False
            record.iface_customer_facing_display = False
            record.iface_print_via_proxy = True
            record.iface_scan_via_proxy = False
            record.iface_big_scrollbars = True
            record.iface_print_auto = True
            record.iface_print_skip_screen = True
            record.iface_tax_included = "total"
            record.iface_display_categ_images = False
            record.proxy_ip = "https://localhost"
            record.iface_tipproduct = False
            record.use_pricelist = True
            record.is_posbox = True
            record.anonymous_partner_id = anonymous_partner.id

    def _check_payment_method_ids(self):
        return

    def open_ui(self):
        res = super().open_ui()
        res["target"] = "new"
        return res

    def _check_currencies(self):
        pass
