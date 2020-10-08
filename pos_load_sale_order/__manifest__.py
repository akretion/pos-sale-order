# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "POS Load Sale Order",
    "version": "12.0.0.1.0",
    "category": "Point Of Sale",
    "author": "Akretion",
    "website": "https://www.akretion.com",
    "license": "AGPL-3",
    "depends": [
        "pos_sale_order",
        "pos_backend_communication",
    ],
    "data": [
        "views/pos_load_sale_order.xml",
        "views/sale_order.xml",
    ],
    "qweb": [
        "static/src/xml/pos_load_sale_order.xml",
    ],
    "demo": [],
    "installable": True,
}
