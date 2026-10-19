# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


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
            if picking.picking_type_id.code == "outgoing" and picking.state not in (
                "done",
                "cancel",
            ):
                for line in picking.move_lines:
                    if line.state != "done":
                        vals.append([0, 0, self._prepare_line(line)])
        return self.create({"line_ids": vals})

    def _get_first_moves(self):
        # NOTE: deliveries of SO could be a mixed of {one,two,three,...} steps operations
        moves = self.line_ids.move_line_id
        first_moves = moves.browse()
        while moves:
            first_moves = moves.move_orig_ids | moves.filtered(
                lambda m: not m.move_orig_ids
            )
            moves = first_moves - moves
        return first_moves

    def _set_moves_qty_done(self, moves):
        for move in moves:
            if move.move_line_ids:
                for line in move.move_line_ids:
                    # Do not change anything if the move line has been created
                    # manually (forced) or if the qty done has already been set
                    if not line.product_qty or line.qty_done:
                        continue
                    line.qty_done = line.product_qty
            elif move.state == "confirmed":  # Ignore 'waiting' moves
                move.quantity_done = move.product_uom_qty

    def _handle_button_validate_action(self, action):
        if action.get("res_model") == "stock.backorder.confirmation":
            ctx = action.get("context", {})
            wiz = self.env[action["res_model"]].with_context(**ctx).create({})
            wiz.process()

    def _validate_delivery(self):
        """Validate all chained stock operations.

        It starts with the first one of the chain following pull rules scheme.

        `UserError` is raised if at least one operation could not be processed.
        """
        first_moves = self._get_first_moves()
        moves_to_validate = first_moves
        while moves_to_validate:
            for picking in moves_to_validate.picking_id:
                if picking.state in ("done", "cancel"):
                    continue
                if picking.state == "confirmed":
                    picking.action_assign()
                self._set_moves_qty_done(moves_to_validate)
                res = picking.button_validate()
                if res is not True:  # Action
                    self._handle_button_validate_action(res)
                if picking.state != "done":
                    raise UserError(
                        _(
                            "Operation %s cannot be validated automatically,"
                            " please do it from delivery menu"
                        )
                        % picking.name
                    )
            moves_to_validate = moves_to_validate.move_dest_ids

    def confirm(self):
        for line in self.line_ids:
            line.move_line_id.quantity_done = line.qty
        self._validate_delivery()
        return True


class PosDeliveryWizardLine(models.TransientModel):
    _name = "pos.delivery.wizard.line"
    _description = "Pos Delivery Wizard Line"

    delivery_id = fields.Many2one("pos.delivery.wizard", "Delivery")
    product_id = fields.Many2one("product.product", "Product")
    move_line_id = fields.Many2one("stock.move", "Move Line")
    qty = fields.Float(digits="Product Unit of Measure")
