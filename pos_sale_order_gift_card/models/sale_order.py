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

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super().create_from_ui(orders, draft=draft)
        for order in res["orders"]:
            gift_cards = self.env["gift.card"].browse()
            for line in self.env["sale.order"].browse(order["id"]).order_line:
                order["name"] = line.order_id.name
                if line.gift_card_ids:
                    gift_cards |= line.gift_card_ids
            order["bought_gift_cards"] = [self._pos_return_gift_cards(g) for g in gift_cards]
        return res

    def _pos_return_gift_cards(self, gift_card):
        return {
                "code": gift_card.code,
                "available_amount": gift_card.available_amount,
                "initial_amount": gift_card.initial_amount,
                "start_date": gift_card.start_date,
                "end_date": gift_card.end_date,
        }
