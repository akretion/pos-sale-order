# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class PosDeliveryWizard(models.TransientModel):
    _name = "pos.delivery.wizard"
    _description = "Pos Delivery Wizard"

    line_ids = fields.One2many("pos.delivery.wizard.line", "delivery_id", "Lines")

    def _prepare_line(self, line):
        return {
            "product_id": line.product_id.id,
            "qty": line.product_uom_qty,
            "move_line_id": line.id,
        }

    def create_wizard(self, sale):
        vals = []
        for picking in sale.picking_ids:
            if picking.picking_type_id.code == "outgoing" and picking.state != "done":
                for line in picking.move_lines:
                    if line.state != "done":
                        vals.append([0, 0, self._prepare_line(line)])
        return self.create({"line_ids": vals})

    def confirm(self):
        for line in self.line_ids:
            line.move_line_id.quantity_done = line.qty
        res = None
        for picking in self.mapped("line_ids.move_line_id.picking_id"):
            result = picking.button_validate()
            if result:
                if res is None:
                    res = result
                else:
                    raise UserError(
                        "Fail to deliver picking have been split, please do it"
                        "from delivery menu"
                    )
        return res


class PosDeliveryWizardLine(models.TransientModel):
    _name = "pos.delivery.wizard.line"
    _description = "Pos Delivery Wizard Line"

    delivery_id = fields.Many2one("pos.delivery.wizard", "Delivery")
    product_id = fields.Many2one("product.product", "Product")
    move_line_id = fields.Many2one("stock.move", "Move Line")
    qty = fields.Float(digits=dp.get_precision("Product Unit of Measure"))
