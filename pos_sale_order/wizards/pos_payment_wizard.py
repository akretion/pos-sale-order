# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class PosPaymentWizard(models.TransientModel):
    _name = "pos.payment.wizard"
    _description = "Pos Payment Wizard"

    amount = fields.Float(digits=dp.get_precision("Product Price"))
    sale_order_id = fields.Many2one("sale.order")
    journal_id = fields.Many2one("account.journal", "Payment mode")
    available_journal_ids = fields.Many2many(
        comodel_name="account.journal", string="Available Journal", readonly=True
    )

    def _get_session(self):
        session = self.env["pos.session"].search(
            [("state", "=", "opened"), ("user_id", "=", self._uid)]
        )
        if not session:
            raise UserError(_("There is no session Opened, please open one"))
        return session

    def create_wizard(self, sale):
        available_journals = self._get_session().mapped("statement_ids.journal_id")
        default_journal = available_journals[0]
        for journal in available_journals:
            if journal.type == "cash":
                default_journal = journal
                break
        vals = {
            "sale_order_id": sale.id,
            "available_journal_ids": [(6, 0, available_journals.ids)],
            "journal_id": default_journal.id,
            "amount": sale.pos_amount_to_pay,
        }
        return self.create(vals)

    def _prepare_statement_line(self):
        session = self._get_session()
        sale = self.sale_order_id
        statement = session.statement_ids.filtered(
            lambda s: s.journal_id == self.journal_id
        )
        name = _("Manual payment {}").format(sale.name)
        partner = sale.partner_invoice_id.commercial_partner_id
        account_def = (
            self.env["ir.property"]
            .with_context(force_company=self.journal_id.company_id.id)
            .get("property_account_receivable_id", "res.partner")
        )
        account = partner.property_account_receivable_id or account_def
        return {
            "amount": self.amount,
            "date": fields.Date.context_today(self),
            "name": name,
            "statement_id": statement.id,
            "journal_id": self.journal_id.id,
            "ref": session.name,
            "partner_id": partner.id,
            "pos_sale_order_id": sale.id,
            "account_id": account.id,
        }

    def pay(self):
        vals = self._prepare_statement_line()
        self.env["account.bank.statement.line"].create(vals)
        return True
