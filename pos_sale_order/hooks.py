# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def pre_init_hook(env):
    openupgrade.load_data(env, "pos_sale_order", "data/res_partner_data.xml")
    env["res.partner"].flush_model()


def post_init_hook(env):
    pass
    # env.ref("point_of_sale.action_client_pos_menu").write(
    #     {"params": {"menu_id": env.ref("pos_sale_order.menu_pos_sale_order_root").id}}
    # )
