# Copyright 2018 Akretion (https://www.akretion.com).
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    account_id = fields.Many2one(
        "account.account", related="journal_id.default_debit_account_id", readonly=True
    )


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    pos_sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order", ondelete="cascade"
    )
