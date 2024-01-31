# Copyright 2020-2024 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PosSessionWizardMixin(models.AbstractModel):
    _name = "pos.session.wizard.mixin"
    _description = "Pos Session Wizard Mixin"

    sale_order_id = fields.Many2one("sale.order")
    payment_method_id = fields.Many2one("pos.payment.method", "Payment method")
    available_payment_method_ids = fields.Many2many(
        comodel_name="pos.payment.method",
        string="Available Payment Method",
        readonly=True,
    )

    def _get_session(self):
        session = self.env["pos.session"].search(
            [
                ("state", "=", "opened"),
                ("user_id", "=", self._uid),
                ("rescue", "=", False),
                ("payment_method_ids", "!=", False),
            ]
        )
        if not session:
            raise UserError(
                _("There is no session opened with payment method, please open one")
            )
        return session

    def _prepare_wizard(self, sale, payment_methods, default_method):
        return {
            "sale_order_id": sale.id,
            "available_payment_method_ids": [(6, 0, payment_methods.ids)],
            "payment_method_id": default_method.id,
        }

    def create_wizard(self, sale):
        payment_methods = self._get_session().payment_method_ids
        default_method = payment_methods[0]
        for method in payment_methods:
            if method.is_cash_count:
                default_method = method
                break

        return self.create(self._prepare_wizard(sale, payment_methods, default_method))
