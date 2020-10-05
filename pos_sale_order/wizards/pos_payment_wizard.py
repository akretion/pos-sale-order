# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class PosPaymentWizard(models.TransientModel):
    _name = "pos.payment.wizard"
    _description = "Pos Payment Wizard"

    amount = fields.Float(
        digits=dp.get_precision("Product Price"), default=lambda s: s._default_amount()
    )
    journal_id = fields.Many2one("account.journal", "Payment mode")
    available_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        string="Available Journal",
        compute="_compute_available_journal_ids",
    )

    def _get_session(self):
        self.ensure_one()
        session = self.env["pos.session"].search(
            [("state", "=", "opened"), ("user_id", "=", self._uid)]
        )
        if not session:
            raise UserError(_("There is no session Opened, please open one"))
        return session

    def _compute_available_journal_ids(self):
        self.available_journal_ids = self._get_session().mapped(
            "statement_ids.journal_id"
        )

    def _default_amount(self):
        record = self._get_record()
        return record.amount_total

    def _get_record(self):
        return self.env[self._context["active_model"]].browse(
            self._context["active_id"]
        )

    def _prepare_statement_line(self):
        session = self._get_session()
        statement = session.statement_ids.filtered(
            lambda s: s.journal_id == self.journal_id
        )
        record = self._get_record()
        name = _("Manual payment {}").format(record.name)
        vals = {
            "amount": self.amount,
            "date": fields.Date.context_today(self),
            "name": name,
            "partner_id": record.partner_id.id,
            "statement_id": statement.id,
            "journal_id": self.journal_id.id,
            "ref": session.name,
        }
        if record._name == "sale.order":
            partner = record.partner_invoice_id.commercial_partner_id
            account_def = (
                self.env["ir.property"]
                .with_context(force_company=self.journal_id.company_id.id)
                .get("property_account_receivable_id", "res.partner")
            )
            account = partner.property_account_receivable_id or account_def
            vals.update(
                {
                    "partner_id": partner.id,
                    "pos_sale_order_id": record.id,
                    "account_id": account.id,
                }
            )
        elif record._name == "account.invoice":
            vals.update(
                {
                    "partner_id": record.partner_id.commercial_partner_id.id,
                    "pos_invoice_id": record.id,
                    "account_id": record.account_id.id,
                }
            )
        return vals

    def pay(self):
        vals = self._prepare_statement_line()
        self.env["account.bank.statement.line"].create(vals)
        return True
