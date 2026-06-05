# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    should_display_pos_warning = fields.Boolean(
        compute="_compute_should_display_pos_warning"
    )
    pos_warning_confirmed = fields.Boolean(
        string="I read and understood the above warning and I confirm that "
        "I want to proceed with the payment anyway."
    )

    @api.depends("line_ids")
    def _compute_should_display_pos_warning(self):
        for wizard in self:
            # Warn if at least one line move is a POS order
            current_moves = self.line_ids.move_id
            current_sale_orders = current_moves.line_ids.sale_line_ids.order_id
            wizard.should_display_pos_warning = bool(current_sale_orders.session_id)
