# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.addons.pos_sale_order.tests.common import CommonCase


class TestOrder(CommonCase):
    def test_compute_commitment_date(self):
        data = self._get_pos_data()
        res = self.env["sale.order"].compute_pos_requested_date(data["data"])
        self.assertEqual(res["date"], str(date.today()))
        self.assertTrue(res["allow_delivery_now"])

    def test_compute_commitment_date_2(self):
        data = self._get_pos_data()
        self.product0.sale_delay = 4
        res = self.env["sale.order"].compute_pos_requested_date(data["data"])
        self.assertEqual(res["date"], str(date.today() + timedelta(days=4)))
        self.assertTrue(res["allow_delivery_now"])

    def test_delivery_now(self):
        data = self._get_pos_data()
        self.product0.pos_delivery_now_allowed = False
        res = self.env["sale.order"].compute_pos_requested_date(data["data"])
        self.assertFalse(res["allow_delivery_now"])
