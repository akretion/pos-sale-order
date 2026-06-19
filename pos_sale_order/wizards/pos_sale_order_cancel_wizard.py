# Copyright 2024 Akretion (https://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosSaleOrderCancelWizard(models.TransientModel):
    _name = "pos.sale.order.cancel.wizard"
    _description = "PoS Sales Order Cancel"
    _inherit = "pos.session.wizard.mixin"

    has_payments = fields.Boolean("Has Payments", readonly=True)

    def _prepare_wizard(self, sale, payment_methods, default_method):
        vals = super()._prepare_wizard(sale, payment_methods, default_method)
        vals["has_payments"] = bool(sale.payment_ids)
        return vals

    def action_cancel(self):
        return self.sale_order_id.with_context(
            {
                "disable_pos_cancel_warning": True,
                "pos_cancel_payment_method_id": self.payment_method_id.id,
            }
        ).action_cancel()
