# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "POS Sale Order Optional Receipt",
    "summary": "Add button to choose whether to print a receipt or not",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/akretion/pos-sale-order",
    "category": "Point of Sale",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["pos_sale_order"],
    "data": ["views/assets.xml"],
    "qweb": [
        "static/src/xml/PrintReceiptToggleButton.xml",
    ],
}
