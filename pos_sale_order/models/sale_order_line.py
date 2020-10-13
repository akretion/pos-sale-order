# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("order_id.session_id")
    def _get_to_invoice_qty(self):
        for record in self:
            if record.order_id.session_id:
                record.qty_to_invoice = record.product_uom_qty - record.qty_invoiced
            else:
                super(SaleOrderLine, record)._get_to_invoice_qty()
