# Copyright 2014 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "POS Only Sale Order",
    "version": "18.0.1.0.0",
    "category": "Point Of Sale",
    "author": "Akretion",
    "website": "https://github.com/akretion/pos-sale-order",
    "license": "AGPL-3",
    "depends": [
        "pos_sale",
        "sale_stock",
        # TODO FIXME
        # "account_reconcile_restrict_partner_mismatch",
        # "web_widget_numeric_step",
        # "sale_delivery_state",
        # "sale_invoice_policy",
        "queue_job",
    ],
    "data": [
        # "security/res_groups.xml",
        # "security/ir.model.access.csv",
        # "wizards/pos_payment_wizard_view.xml",
        # "wizards/pos_delivery_wizard_view.xml",
        # "views/sale_view.xml",
        # "views/pos_payment_method_views.xml",
        # "views/point_of_sale_view.xml",
        # "views/menu.xml",
        # "views/account_moves_lines.xml",
        # "views/pos_payment_view.xml",
        # "data/res_partner_data.xml",
        # "data/pos_config_data.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "pre_init_hook": "pre_init_hook",
}
