# Copyright 2014 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class PosInvoiceReport(models.AbstractModel):
    _inherit = "report.point_of_sale.report_invoice"

    @api.model
    def _get_report_values(self, docids, data=None):
        sales = self.env["sale.order"].browse(docids)
        missings = sales.filtered(lambda o: not o.invoice_ids)
        if missings:
            raise UserError(
                _("No link to an invoice for %s.") % ", ".join(missings.mapped("name"))
            )
        ids_to_print = sales.mapped("invoice_ids").ids
        return {
            "docs": self.env["account.move"].sudo().browse(ids_to_print),
            "qr_code_urls": self.env["report.account.report_invoice"]
            .sudo()
            ._get_report_values(ids_to_print)["qr_code_urls"],
        }
