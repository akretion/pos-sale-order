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
        "sale_quick_payment",
        "account_bank_statement_sale_order",
    ],
    "data": [
        "views/sale_view.xml",
        "views/point_of_sale_view.xml",
        "data/res_partner_data.xml",
        "data/pos_config_data.xml",
    ],
    "demo": [],
    "installable": True,
}
