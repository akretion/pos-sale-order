# Copyright 2014 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "POS Only Sale Order",
    "version": "12.0.0.1.0",
    "category": "Point Of Sale",
    "author": "Akretion",
    "website": "http://www.akretion.com",
    "license": "AGPL-3",
    "depends": [
        "point_of_sale",
        "sale",
        "account_reconcile_restrict_partner_mismatch",
        "web_widget_numeric_step",
        "sale_delivery_state",
    ],
    "data": [
        "security/res_groups.xml",
        "wizards/pos_payment_wizard_view.xml",
        "wizards/pos_delivery_wizard_view.xml",
        "views/sale_view.xml",
        "views/point_of_sale_view.xml",
        "views/menu.xml",
        "data/res_partner_data.xml",
        "data/pos_config_data.xml",
        "templates/assets.xml",
    ],
    "demo": [],
    "installable": True,
    "post_init_hook": "post_init_hook",
}