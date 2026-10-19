# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pos_receipt_printed = fields.Boolean(
        help="Whether the receipt has been printed or not by the POS",
        default=True,
        readonly=True,
    )

    @api.model
    def import_one_pos_order(self, order, draft=False):
        sale = super().import_one_pos_order(order, draft=draft)
        if order.get("data", {}).get("no_receipt"):
            sale.pos_receipt_printed = False
        return sale

    def _get_receipts(self):
        receipts = []
        for record in self:
            if record.pos_receipt_printed:
                receipts.extend(super(SaleOrder, record)._get_receipts())
        return receipts
