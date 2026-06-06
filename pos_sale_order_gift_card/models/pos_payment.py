# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PoSPayment(models.Model):
    _inherit = "pos.payment"

    def _set_gift_card_line(self, values):
        gift_card_line = super()._set_gift_card_line(values)
        if gift_card_line:
            gift_card_line.sale_order_ids = [(6, 0, self.pos_sale_order_id.ids)]
            gift_card_line.pos_payment_id = self.id
