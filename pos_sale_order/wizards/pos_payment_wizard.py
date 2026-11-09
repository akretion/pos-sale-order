# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PosPaymentWizard(models.TransientModel):
    _name = "pos.payment.wizard"
    _description = "Pos Payment Wizard"
    _inherit = "pos.session.wizard.mixin"

    amount = fields.Float(digits="Product Price")

    def _prepare_wizard(self, sale, payment_methods, default_method):
        vals = super()._prepare_wizard(sale, payment_methods, default_method)
        vals["amount"] = sale.pos_amount_to_pay
        return vals

    def _prepare_payment(self):
        session = self._get_session()
        sale = self.sale_order_id
        # The payment must be reconcile with the invoice of the sale order
        # during the session closing. So if the sale is not invoiced we need to
        # - attach the sale order to the current pos session (so it will be invoiced)
        # - force the invoice policy to "order" the all qty will be invoiced
        if not sale.is_invoiced:
            sale.write({"session_id": session.id, "invoice_policy": "order"})
        return {
            "amount": self.amount,
            "name": _("Manual payment {}").format(sale.name),
            "payment_method_id": self.payment_method_id.id,
            "pos_sale_order_id": sale.id,
            "session_id": session.id,
        }

    def pay(self):
        if not self.amount:
            raise UserError(_("Amount must be superior to 0"))
        vals = self._prepare_payment()
        self.env["pos.payment"].create(vals)
        return True
