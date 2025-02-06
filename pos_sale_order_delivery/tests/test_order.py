# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.tests.common import tagged

from odoo.addons.pos_sale_order.tests.common import CommonCase


@tagged("-at_install", "post_install")
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


@tagged("-at_install", "post_install")
class TestOrderStock(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent_location = cls.company_data["default_warehouse"].lot_stock_id
        cls.stock_location_rack = cls.env["stock.location"].create(
            {
                "name": "Rack",
                "location_id": cls.parent_location.id,
            }
        )
        inventory = cls.env["stock.inventory"].create(
            {"name": "Initial inventory adjustment"}
        )
        uom = cls.env.ref("uom.product_uom_unit")
        cls.env["stock.inventory.line"].create(
            {
                "product_id": cls.product0.id,
                "product_uom_id": uom.id,
                "inventory_id": inventory.id,
                "product_qty": 2,
                "location_id": cls.stock_location_components.id,
            }
        )
        cls.env["stock.inventory.line"].create(
            {
                "product_id": cls.product0.id,
                "product_uom_id": uom.id,
                "inventory_id": inventory.id,
                "product_qty": 3,
                "location_id": cls.stock_location_rack.id,
            }
        )
        cls.env["stock.inventory.line"].create(
            {
                "product_id": cls.product1.id,
                "product_uom_id": uom.id,
                "inventory_id": inventory.id,
                "product_qty": 10,
                "location_id": cls.stock_location_rack.id,
            }
        )
        cls.env["stock.inventory.line"].create(
            {
                "product_id": cls.product2.id,
                "product_uom_id": uom.id,
                "inventory_id": inventory.id,
                "product_qty": 1,
                "location_id": cls.stock_location_components.id,
            }
        )
        cls.env["stock.inventory.line"].create(
            {
                "product_id": cls.product2.id,
                "product_uom_id": uom.id,
                "inventory_id": inventory.id,
                "product_qty": 1,
                "location_id": cls.stock_location_rack.id,
            }
        )
        inventory._action_start()
        inventory.action_validate()

    def test_delivery_auto_delivery_stock_ok(self):
        data = self._get_pos_data(
            lines=[
                (self.product0, 5),
                (self.product1, 10),
                (self.product2, 2),
            ]
        )
        so = self._create_sale([data])
        self.assertEqual(len(so), 1)
        self.assertEqual(self.product0.qty_available, 5)
        self.assertEqual(self.product1.qty_available, 10)
        self.assertEqual(self.product2.qty_available, 2)
        so.with_context(test_queue_job_no_delay=True).action_confirm()
        self.assertEqual(so.picking_ids.state, "done")
        # Ensure that the right stock location is decremented
        self.assertEqual(self.product0.qty_available, 0)
        self.assertEqual(self.product1.qty_available, 0)
        self.assertEqual(self.product2.qty_available, 0)
        qty = self.env["stock.quant"]._get_available_quantity
        for p in (self.product0, self.product1, self.product2):
            self.assertEqual(
                qty(p, self.parent_location),
                0,
            )
            self.assertEqual(
                qty(p, self.stock_location_components),
                0,
            )

    def test_delivery_auto_delivery_stock_missing(self):
        data = self._get_pos_data(
            lines=[
                (self.product1, 20),
            ]
        )
        so = self._create_sale([data])
        self.assertEqual(len(so), 1)
        self.assertEqual(self.product1.qty_available, 10)
        so.with_context(test_queue_job_no_delay=True).action_confirm()
        self.assertEqual(so.picking_ids.state, "done")
        # Ensure that the right stock location is decremented
        self.assertEqual(self.product1.qty_available, -10)
        qty = self.env["stock.quant"]._get_available_quantity
        self.assertEqual(
            qty(self.product1, self.parent_location),
            0,
        )
        self.assertEqual(
            qty(self.product1, self.stock_location_components),
            0,
        )

    def test_delivery_auto_delivery_stock_missing_multi_location(self):
        data = self._get_pos_data(
            lines=[
                (self.product0, 10),
            ]
        )
        so = self._create_sale([data])
        self.assertEqual(len(so), 1)
        self.assertEqual(self.product0.qty_available, 5)
        so.with_context(test_queue_job_no_delay=True).action_confirm()
        self.assertEqual(so.picking_ids.state, "done")
        # Ensure that the right stock location is decremented
        self.assertEqual(self.product0.qty_available, -5)
        qty = self.env["stock.quant"]._get_available_quantity
        self.assertEqual(
            qty(self.product0, self.parent_location),
            0,
        )
        self.assertEqual(
            qty(self.product0, self.stock_location_components),
            0,
        )
        self.assertEqual(
            qty(self.product0, self.stock_location_rack),
            0,
        )
