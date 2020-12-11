# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "POS Sale Order Load",
    "version": "14.0.1.0.0",
    "category": "Point Of Sale",
    "author": "Akretion",
    "website": "https://github.com/akretion/pos-sale-order",
    "license": "AGPL-3",
    "depends": ["pos_sale_order", "pos_backend_communication"],
    "data": ["views/pos_sale_order_load.xml", "views/sale_order.xml"],
    "qweb": ["static/src/xml/pos_sale_order_load.xml"],
    "demo": [],
    "installable": True,
}
