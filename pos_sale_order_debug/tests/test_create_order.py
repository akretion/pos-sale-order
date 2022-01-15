# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import mute_logger

from odoo.addons.pos_sale_order.tests.common import CommonCase


class TestCreateOrder(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = cls._get_pos_data()
        # remove required fields
        cls.ori_pricelist_id = cls.data["data"].pop("pricelist_id")

        # odoo test put a datetime as name this raise an issue when converting to json
        cls.data["data"]["statement_ids"][0][2]["name"] = "2021-01-01 00:00:00"

    @mute_logger("odoo.addons.pos_sale_order.models.sale_order")
    def test_create_sale(self):
        self._create_sale([self.data])

        error = self.env["pos.sale.error"].search([])
        self.assertEqual(len(error), 1)

        self._create_sale([self.data])
        error = self.env["pos.sale.error"].search([])
        self.assertEqual(len(error), 1)

    @mute_logger("odoo.addons.pos_sale_order.models.sale_order")
    def test_create_sale_missing_session(self):
        data = self._get_pos_data()
        data["data"]["statement_ids"][0][2]["name"] = "2021-01-01 00:00:00"
        data["data"]["pos_session_id"] += 1000
        self._create_sale([data])
        error = self.env["pos.sale.error"].search([])
        self.assertEqual(len(error), 1)
        self.assertFalse(error.pos_session_id)

    @mute_logger("odoo.addons.pos_sale_order.models.sale_order")
    def test_rerun_failed(self):
        self._create_sale([self.data])
        error = self.env["pos.sale.error"].search([])
        data = error.data
        data["data"]["pricelist_id"] = self.ori_pricelist_id
        error.data = data
        error.run()
        self.assertEqual(len(error.order_id), 1)
