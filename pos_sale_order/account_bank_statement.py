# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from openerp import fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    account_id = fields.Many2one(
        'account.account',
        related='journal_id.default_debit_account_id',
        readonly=True)


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    pos_so_statement_id = fields.Many2one(
        'sale.order', string="POS SO statement",
        ondelete='cascade')
