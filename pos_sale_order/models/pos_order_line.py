# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _adapt_vals_to_sale_line(self, vals, mode):
        for key in list(vals.keys()):
            if key not in self.env["sale.order.line"]._fields:
                _logger.warning(
                    "The field %s is not present in sale.order.line, it will be removed from the vals dict for the %s operation",
                    key,
                    mode,
                )
                del vals[key]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return self.env["sale.order.line"].create(
            [self._adapt_vals_to_sale_line(vals, "create") for vals in vals_list]
        )

    def write(self, vals):
        return self.env["sale.order.line"].write(
            self._adapt_vals_to_sale_line(vals, "write")
        )

    def browse(self, ids=()):
        return self.env["sale.order.line"].browse(ids)

    def read(self, fields=None, load="_classic_read"):
        if fields:
            fields = [field for field in self.env["sale.order.line"]._fields]
        return self.env["sale.order.line"].read(fields, load)

    def search_read(
        self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs
    ):
        if fields:
            fields = [field for field in self.env["sale.order.line"]._fields]
        return self.env["sale.order.line"].search_read(
            domain, fields, offset, limit, order, **read_kwargs
        )
