# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super()._payment_fields(order, ui_paymentline)
        fields.update(
            {
                "gift_card_id": ui_paymentline.get("gift_card_id"),
            }
        )
        return fields
