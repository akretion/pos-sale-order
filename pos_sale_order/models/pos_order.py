# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _adapt_vals_to_sale(self, vals, mode):
        def adapt(command, method):
            if len(command) == 3 and isinstance(command[2], dict):
                return [
                    command[0],
                    command[1],
                    method(command[2], mode),
                ]
            return command

        if "lines" in vals:
            vals["order_line"] = [
                adapt(command, self.env["pos.order.line"]._adapt_vals_to_sale_line)
                for command in vals.pop("lines")
            ]

        if "payment_ids" in vals:
            vals["payment_ids"] = [
                adapt(command, self.env["pos.payment"]._adapt_vals_to_payment)
                for command in vals.pop("payment_ids")
            ]
        for key in list(vals.keys()):
            if key not in self.env["sale.order"]._fields:
                _logger.warning(
                    "The field %s is not present in sale.order, it will be removed from the vals dict for the %s operation",
                    key,
                    mode,
                )
                del vals[key]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return self.env["sale.order"].create(
            [self._adapt_vals_to_sale(vals, "create") for vals in vals_list]
        )

    def write(self, vals):
        return self.env["sale.order"].write(self._adapt_vals_to_sale(vals, "write"))

    def browse(self, ids=()):
        return self.env["sale.order"].browse(ids)

    def read(self, fields=None, load="_classic_read"):
        if fields:
            fields = [field for field in self.env["sale.order"]._fields]
        return self.env["sale.order"].read(fields, load)

    def search_read(
        self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs
    ):
        if fields:
            fields = [field for field in self.env["sale.order"]._fields]
        return self.env["sale.order"].search_read(
            domain, fields, offset, limit, order, **read_kwargs
        )
