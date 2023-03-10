# Copyright 2020 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "POS Sale Order No Payment",
    "version": "14.0.1.0.1",
    "category": "Point Of Sale",
    "author": "Akretion",
    "website": "https://github.com/akretion/pos-sale-order",
    "license": "AGPL-3",
    "depends": [
        "pos_sale_order",
    ],
    "data": [
        "templates/assets.xml",
        "views/product_pricelist.xml",
    ],
    "qweb": [
        "static/src/xml/QuotationButton.xml",
        "static/src/xml/PaymentScreen.xml",
        "static/src/xml/PaymentScreenStatus.xml",
        "static/src/xml/PaymentScreenNumpad.xml",
    ],
    "installable": True,
}
