# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Pos Sale Order Debug",
    "summary": "In case a sync error a item is stored on backend to replay it easily",
    "version": "14.0.1.0.0",
    "category": "Pos Sale Order",
    "website": "https://github.com/akretion/pos-sale-order",
    "author": " Akretion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "pos_sale_order",
        "base_sparse_field",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/pos_sale_error_view.xml",
    ],
    "demo": [],
}
