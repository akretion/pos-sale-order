# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.pos_sale_order.tests.common import CommonCase


class TestCreateOrder(CommonCase):
    def test_export_sale(self):
        data = self._get_pos_data()
        sales = self._create_sale([data])
        ori = data["data"]
        expected_data = {
            "name": sales.name,
            "partner_id": ori["partner_id"],
            "partner_name": sales.partner_id.name,
            "uid": sales.id,
            "pricelist_id": ori["pricelist_id"],
            "statement_ids": [],
            "sequence_number": 1,
            "sale_order_id": sales.id,
            "sale_order_name": sales.name,
            "fiscal_position_id": False,
            "creation_date": ori["creation_date"],
            "lines": [
                [
                    0,
                    0,
                    {
                        "product_id": ori["lines"][0][2]["product_id"],
                        "price_unit": 10.0,
                        "qty": 3.0,
                        "pack_lot_ids": [],
                        "discount": 0.0,
                        "id": sales.order_line[0].id,
                    },
                ],
                [
                    0,
                    0,
                    {
                        "product_id": ori["lines"][1][2]["product_id"],
                        "price_unit": 5.0,
                        "qty": 1.0,
                        "pack_lot_ids": [],
                        "discount": 0.0,
                        "id": sales.order_line[1].id,
                    },
                ],
                [
                    0,
                    0,
                    {
                        "product_id": ori["lines"][2][2]["product_id"],
                        "price_unit": 15.0,
                        "qty": 2.0,
                        "pack_lot_ids": [],
                        "discount": 0.0,
                        "id": sales.order_line[2].id,
                    },
                ],
            ],
        }
        exported_data = sales._pos_json()["data"]
        self.maxDiff = None
        # TODO date do not have exactly the same format
        # check if it's an issue or not
        expected_data.pop("creation_date")
        exported_data.pop("creation_date")
        self.assertEqual(expected_data, exported_data)

    def test_update_sale(self):
        # TODO
        pass
