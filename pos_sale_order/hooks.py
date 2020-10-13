# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref("point_of_sale.action_client_pos_menu").write(
        {"params": {"menu_id": env.ref("pos_sale_order.menu_pos_sale_order_root").id}}
    )
