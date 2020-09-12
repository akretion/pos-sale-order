# Copyright 2014 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class PosInvoiceReport(models.AbstractModel):
    _inherit = "report.point_of_sale.report_invoice"

    @api.multi
    def render_html(self, data):
        report_obj = self.env["report"]
        posorder_obj = self.env["sale.order"]
        report = report_obj._get_report_from_name("account.report_invoice")
        selected_orders = posorder_obj.browse(self.ids)

        ids_to_print = []
        invoiced_posorders_ids = []
        for order in selected_orders:
            if order.invoice_ids:
                ids_to_print.append(order.invoice_ids.id)
                invoiced_posorders_ids.append(order.id)

        not_invoiced_orders_ids = list(set() - set(invoiced_posorders_ids))
        if not_invoiced_orders_ids:
            not_invoiced_posorders = posorder_obj.browse(not_invoiced_orders_ids)
            not_invoiced_orders_names = list(
                map(lambda a: a.name, not_invoiced_posorders)
            )
            raise UserError(
                _("Error!"),
                _(
                    "No link to an invoice for %s."
                    % ", ".join(not_invoiced_orders_names)
                ),
            )

        docargs = {
            "doc_ids": ids_to_print,
            "doc_model": report.model,
            "docs": selected_orders,
        }
        return report_obj.render("account.report_invoice", docargs)
