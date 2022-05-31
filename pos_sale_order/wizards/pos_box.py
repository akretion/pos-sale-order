# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CashBoxOut(models.TransientModel):
    _inherit = "cash.box.out"

    # Odoo do not set the counterpart account and do not want to set it
    # it's just crazy: https://github.com/odoo/odoo/pull/82568
    def _calculate_values_for_statement_line(self, record):
        values = super()._calculate_values_for_statement_line(record)
        values[
            "counterpart_account_id"
        ] = record.journal_id.company_id.transfer_account_id.id
        return values
