# Copyright 2023 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_cash_register_counterpart_account(self):
        super()._get_cash_register_counterpart_account()

        # In pos_sale_order, the cash register is attached to the company
        # transfer account:
        # https://github.com/akretion/pos-sale-order/blob/14.0/pos_sale_order\
        # /wizards/pos_box.py#L17
        return self.company_id.transfer_account_id
