# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_analytic_account_id(self):
        super()._compute_analytic_account_id()
        for record in self:
            if record.config_id and record.config_id.account_analytic_id:
                record.analytic_account_id = record.config_id.account_analytic_id
