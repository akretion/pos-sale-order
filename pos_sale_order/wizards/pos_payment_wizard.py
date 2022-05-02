# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PosPaymentWizard(models.TransientModel):
    _name = "pos.payment.wizard"
    _description = "Pos Payment Wizard"

    amount = fields.Float(digits="Product Price")
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
                _("There is no session Opened with payment method, please open one")
            )
        return session

    def create_wizard(self, sale):
        payment_methods = self._get_session().payment_method_ids
        default_method = payment_methods[0]
        for method in payment_methods:
            if method.is_cash_count:
                default_method = method
                break
        vals = {
            "sale_order_id": sale.id,
            "available_payment_method_ids": [(6, 0, payment_methods.ids)],
            "payment_method_id": default_method.id,
            "amount": sale.pos_amount_to_pay,
        }
        return self.create(vals)

    def _prepare_payment(self):
        session = self._get_session()
        sale = self.sale_order_id
        return {
            "amount": self.amount,
            "name": _("Manual payment {}").format(sale.name),
            "payment_method_id": self.payment_method_id.id,
            "pos_sale_order_id": sale.id,
            "session_id": session.id,
        }

    def pay(self):
        vals = self._prepare_payment()
        self.env["pos.payment"].create(vals)
        return True
