# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _adapt_vals_to_sale_line(self, vals, mode, from_=None):
        if from_ and "order_id" in vals:
            vals.pop("order_id")
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
        return self.env["sale.order.line"].read(fields, load)

    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        pos_domain = [("order_id.session_id", "!=", False)]
        if domain:
            pos_domain = expression.AND([pos_domain, domain])
        else:
            domain = pos_domain
        return self.env["sale.order.line"].search_fetch(
            domain, field_names, offset, limit, order
        )
