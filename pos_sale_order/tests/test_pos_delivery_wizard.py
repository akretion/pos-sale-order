# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import tagged

from .common import CommonCase


@tagged("-at_install", "post_install")
class TestPosDeliveryWizard(CommonCase):
    def test_create_wizard_from_sale(self):
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        for line in wizard.line_ids:
            self.assertEqual(line.qty, line.move_line_id.product_uom_qty)
            self.assertEqual(line.product_id, line.move_line_id.product_id)

    def test_create_wizard_exclude_done_picking(self):
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        for picking in sale.picking_ids:
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.button_validate()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 0)

    def test_create_wizard_exclude_cancel_picking(self):
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        for picking in sale.picking_ids:
            picking.action_cancel()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 0)

    def test_confirm_wizard(self):
        """Test basic delivery."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, line.qty)
        for picking in sale.picking_ids:
            self.assertEqual(picking.state, "done")

    def test_confirm_wizard_partial_delivery(self):
        """Test partial delivery."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        delivery = sale.picking_ids
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        # Remove one product from the delivery
        move_to_skip = wizard.line_ids[-1].move_line_id
        current_picking = move_to_skip.picking_id
        wizard.line_ids[-1].unlink()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        # Check delivery
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, line.qty)
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(delivery.state, "done")
        # Unprocessed move has been put in a backorder
        backorder = delivery.backorder_ids
        self.assertEqual(backorder.state, "confirmed")
        self.assertIn(move_to_skip, backorder.move_lines)
        self.assertEqual(move_to_skip.quantity_done, 0)
        self.assertNotEqual(move_to_skip.picking_id, current_picking)

    def test_confirm_wizard_partial_qty_delivery(self):
        """Test partial qty delivery."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        delivery = sale.picking_ids
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        # Ship 1 unit over 2
        line_product2 = wizard.line_ids.filtered(
            lambda l: l.product_id == self.product2
        )
        move_product2 = line_product2.move_line_id
        line_product2.qty = 1  # Ship 1 unit instead of 2
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        # Check delivery
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(delivery.state, "done")
        self.assertEqual(move_product2.quantity_done, 1)
        self.assertEqual(move_product2.product_uom_qty, 1)
        # Unprocessed qty has been put in a backorder
        backorder = delivery.backorder_ids
        self.assertEqual(backorder.state, "confirmed")
        self.assertEqual(backorder.move_lines.product_id, self.product2)
        self.assertEqual(backorder.move_lines.product_uom_qty, 1)

    def test_confirm_wizard_with_pick_ship_delivery(self):
        """Test multi-steps delivery (pick+ship)."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.warehouse_id.delivery_steps = "pick_ship"
        sale.action_confirm()
        location = sale.warehouse_id.lot_stock_id
        for product in sale.picking_ids.product_id:
            self.env["stock.quant"]._update_available_quantity(product, location, 100)
        sale.picking_ids.action_assign()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        # Remove one product from the delivery
        move_to_skip = wizard.line_ids[-1].move_line_id
        current_picking = move_to_skip.picking_id
        wizard.line_ids[-1].unlink()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, line.qty)
        # Unprocessed move has been put in a backorder
        self.assertEqual(move_to_skip.quantity_done, 0)
        self.assertNotEqual(move_to_skip.picking_id, current_picking)
        self.assertEqual(len(sale.picking_ids), 4)
        deliveries = sale.picking_ids.filtered(
            lambda p: p.picking_type_code == "outgoing"
        )
        self.assertEqual(len(deliveries), 2)
        self.assertTrue("waiting" in deliveries.mapped("state"))
        self.assertTrue("done" in deliveries.mapped("state"))

    def test_confirm_wizard_with_pick_ship_partial_delivery(self):
        """Test multi-steps partial delivery (pick+ship)."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.warehouse_id.delivery_steps = "pick_ship"
        sale.action_confirm()
        location = sale.warehouse_id.lot_stock_id
        for product in sale.picking_ids.product_id:
            self.env["stock.quant"]._update_available_quantity(product, location, 100)
        sale.picking_ids.action_assign()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, line.qty)
        for picking in sale.picking_ids:
            self.assertEqual(picking.state, "done")

    def test_confirm_wizard_with_pick_pack_ship_delivery(self):
        """Test multi-steps delivery (pick+pack+ship)."""
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.warehouse_id.delivery_steps = "pick_pack_ship"
        sale.action_confirm()
        location = sale.warehouse_id.lot_stock_id
        for product in sale.picking_ids.product_id:
            self.env["stock.quant"]._update_available_quantity(product, location, 100)
        sale.picking_ids.action_assign()
        wizard = self.env["pos.delivery.wizard"].create_wizard(sale)
        self.assertEqual(len(wizard.line_ids), 3)
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, 0)
        wizard.confirm()
        for line in wizard.line_ids:
            self.assertEqual(line.move_line_id.quantity_done, line.qty)
        for picking in sale.picking_ids:
            self.assertEqual(picking.state, "done")

    def test_open_pos_delivery_wizard(self):
        data = self._get_pos_data()
        sale = self._create_sale([data])
        sale.action_confirm()
        action = sale.open_pos_delivery_wizard()
        self.assertIn("res_id", action)
        wizard = self.env["pos.delivery.wizard"].browse(action["res_id"])
        self.assertEqual(len(wizard.line_ids), 3)
