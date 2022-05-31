# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests.common import tagged

from odoo.addons.pos_sale_order.tests.common import CommonCase


@tagged("-at_install", "post_install")
class TestClosingSession(CommonCase):
    @classmethod
    def _create_session_sale(cls, pos_session=None):
        data = cls._get_pos_data(pos_session=pos_session)
        data["data"]["is_quotation"] = True
        data["data"]["statement_ids"] = []
        datas = [
            data,
            cls._get_pos_data(pos_session=pos_session, amount_return=5),
            cls._get_pos_data(partner=cls.partner_3, pos_session=pos_session),
            cls._get_pos_data(partner=cls.partner_3, pos_session=pos_session),
            cls._get_pos_data(partner=cls.partner_2, pos_session=pos_session),
            cls._get_pos_data(
                partner=cls.partner_2, pos_session=pos_session, to_invoice=True
            ),
        ]
        return cls._create_sale(datas)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sales = cls._create_session_sale()

    def _check_invoice_number(self, invoices, expected):
        def count_inv(invoices, partner):
            return len(invoices.filtered(lambda s: s.partner_id == partner))

        for partner, qty in expected:
            self.assertEqual(count_inv(invoices, partner), qty)

    def test_close_session(self):
        # We expect 4 invoices
        # - one invoice for anonymous SO
        # - one for the partner 3
        # - two for the partner 2
        # - first sale should be still in draft

        self._close_session()
        self.assertEqual(self.sales[0].state, "draft")
        self.assertEqual(set(self.sales[1:].mapped("state")), {"sale"})

        self.assertEqual(self.sales[0].invoice_status, "no")
        self.assertEqual(set(self.sales[1:].mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.invoice_ids
        self.assertEqual(self.pos_session.invoice_ids, invoices)
        self.assertEqual(len(invoices), 4)

        self._check_invoice_number(
            invoices,
            [(self.partner_2, 2), (self.partner_3, 1), (self.partner_anonymous, 1)],
        )

        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(set(invoices.mapped("payment_state")), {"paid"})

        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 3 payment (one per partner)
        self.assertEqual(len(move), 3)
        self.assertEqual(sum(move.mapped("amount_total")), 325)
