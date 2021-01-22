# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("pricelist_id.pos_allow_payment")
    def _compute_pos_payment(self):
        record_with_payment = self.filtered("pricelist_id.pos_allow_payment")
        record_without_payment = self - record_with_payment
        record_without_payment.update({"pos_payment_state": "none"})
        return super(SaleOrder, record_with_payment)._compute_pos_payment()

    def _confirm_pos_order(self, order):
        if order["data"].get("is_quotation"):
            return
        else:
            return super()._confirm_pos_order(order)
