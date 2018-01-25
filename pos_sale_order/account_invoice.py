# -*- coding: utf-8 -*-
# © 2016 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import itertools
from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    pos_anonyme_invoice = fields.Boolean()

    @api.multi
    def reconcile(self, payemnt_move_ids,
                  writeoff_acc_id, writeoff_period_id, writeoff_journal_id):
        # TODO check if we can use different period for
        # payment and the writeoff line
        self.ensure_one()

        move_ids = (payemnt_move_ids | self.move_id).ids
        self._cr.execute(
            "SELECT id FROM account_move_line WHERE move_id IN %s",
            (tuple(move_ids), ))
        lines = self.env['account.move.line'].browse(
            [r[0] for r in self._cr.fetchall()])
        lines2rec = lines.browse()
        total = 0.0
        for line in itertools.chain(lines, self.payment_ids):
            if line.account_id == self.account_id:
                lines2rec += line
                total += (line.debit or 0.0) - (line.credit or 0.0)

        if not round(total, self.env['decimal.precision'].precision_get(
                'Account')) or writeoff_acc_id:
            lines2rec.reconcile(
                'manual', writeoff_acc_id, writeoff_period_id,
                writeoff_journal_id)
        else:
            code = self.currency_id.symbol
            # TODO: use currency's formatting function
            msg = (_("Invoice partially paid: %s%s of %s%s (%s%s remaining).") % (0, code, self.amount_total, code, total, code))
            self.message_post(body=msg)
            lines2rec.reconcile_partial('manual')

        # Update the stored value (fields.function), so we write to trigger recompute
        return self.write({})