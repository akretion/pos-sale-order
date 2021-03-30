# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    cash_journal_id = fields.Many2one(
        string="Journal", help="Journal used for generating payment"
    )
    split_transactions = fields.Boolean(
        help="If ticked, each payment will generate a separated journal item."
    )
