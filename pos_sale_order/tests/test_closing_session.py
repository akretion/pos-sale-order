# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.queue_job.job import Job

from .common import CommonCase


class TestClosingSession(CommonCase):
    @classmethod
    def _create_session_sale(cls, pos_session=None):
        datas = [
            cls._get_pos_data(pos_session=pos_session),
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

    def _check_closing_session(self):
        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

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
        self.assertEqual(sum(move.mapped("amount_total")), 390)

    def test_close_session(self):
        # We expect 4 invoices
        # - one invoice for anonymous SO
        # - one for the partner 3
        # - two for the partner 2
        self._close_session()
        self._check_closing_session()

    def test_no_cash_payment(self):
        """Ensure that payment are generated even for no cash payment"""
        # use _write as write is forbidden with open session
        self.cash_pm._write({"is_cash_count": False})
        self._close_session()
        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 3 payment (one per partner)
        self.assertEqual(len(move), 3)
        self.assertEqual(sum(move.mapped("amount_total")), 390)

    def test_split_transaction_payment(self):
        """Ensure that payment are generated even for no cash payment"""
        # use _write as write is forbidden with open session
        self.cash_pm._write({"split_transactions": True})
        self._close_session()
        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 6 payment (one per sale)
        self.assertEqual(len(move), 6)
        self.assertEqual(sum(move.mapped("amount_total")), 390)

    def test_change_partner_and_close(self):
        # We expect 5 invoices
        # - one invoice for anonymous SO
        # - one for the partner 4
        # - one for the partner 3
        # - two for the partner 2
        self.sales[0].write(
            {
                "partner_id": self.partner_4.id,
                "partner_invoice_id": self.partner_4.id,
                "partner_shipping_id": self.partner_4.id,
            }
        )
        self._close_session()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.invoice_ids
        self.assertEqual(self.pos_session.invoice_ids, invoices)
        self.assertEqual(len(invoices), 5)

        self._check_invoice_number(
            invoices,
            [
                (self.partner_2, 2),
                (self.partner_3, 1),
                (self.partner_4, 1),
                (self.partner_anonymous, 1),
            ],
        )
        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(set(invoices.mapped("payment_state")), {"paid"})

    def test_change_partner_and_backoffice_invoice_and_close(self):
        # We expect 5 invoices
        # - one invoice for anonymous SO
        # - one for the partner 4
        # - one for the partner 3
        # - two for the partner 2

        sale = self.sales[0]
        sale.write(
            {
                "partner_id": self.partner_4.id,
                "partner_invoice_id": self.partner_4.id,
                "partner_shipping_id": self.partner_4.id,
            }
        )
        sale.action_confirm()
        invoices = sale._create_invoices()
        invoices.action_post()

        self._close_session()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.invoice_ids
        self.assertEqual(self.pos_session.invoice_ids, invoices)
        self.assertEqual(len(invoices), 5)

        self._check_invoice_number(
            invoices,
            [
                (self.partner_2, 2),
                (self.partner_3, 1),
                (self.partner_4, 1),
                (self.partner_anonymous, 1),
            ],
        )

        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(set(invoices.mapped("payment_state")), {"paid"})

    def test_backoffice_invoice_and_change_partner_and_close(self):
        # We expect 5 invoices
        # - one invoice for anonymous SO
        # - one for the partner 4
        # - one for the partner 3
        # - two for the partner 2

        sale = self.sales[0]
        sale.action_confirm()
        invoices = sale._create_invoices()
        invoices.write({"partner_id": self.partner_4.id})
        invoices.action_post()

        self._close_session()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.invoice_ids
        self.assertEqual(self.pos_session.invoice_ids, invoices)
        self.assertEqual(len(invoices), 5)

        self._check_invoice_number(
            invoices,
            [
                (self.partner_2, 2),
                (self.partner_3, 1),
                (self.partner_4, 1),
                (self.partner_anonymous, 1),
            ],
        )
        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(set(invoices.mapped("payment_state")), {"paid"})

    def test_backoffice_payment_sale_order(self):
        # create an order without payment
        data = self._get_pos_data()
        data["data"]["statement_ids"] = []
        sale = self._create_sale([data])
        self._close_session()

        # Open a new session
        self.config.open_session_cb(check_coa=False)
        self.pos_session = self.config.current_session_id
        self._create_session_sale(pos_session=self.pos_session)

        # Register a backoffice payment on sale order
        wizard = self.env["pos.payment.wizard"].create_wizard(sale)
        self.assertEqual(
            wizard.available_payment_method_ids, self.config.payment_method_ids
        )
        wizard.payment_method_id = self.cash_pm

        wizard.pay()
        self.assertEqual(len(sale.payment_ids), 1)

        # Close the session and check the invoice linked to the sale order
        self._close_session()
        self.assertEqual(sale.invoice_ids.state, "posted")
        self.assertEqual(sale.invoice_ids.payment_state, "paid")

        # Odoo can create rescue session if we do something wrong
        # Ensure that is not the case
        session = self.env["pos.session"].search([("rescue", "=", True)])
        self.assertFalse(session)

    def test_job(self):
        self.assertEqual(
            self.sales.mapped("state"),
            ["draft", "draft", "draft", "draft", "draft", "sale"],
        )
        jobs = self.env["queue.job"].search([])
        self.assertEqual(len(jobs), 5)
        for job in jobs:
            Job.load(self.env, job.uuid).perform()
        self.assertEqual(set(self.sales.mapped("state")), {"sale"})
        self._close_session()
        self._check_closing_session()

    def test_job_execute_after_closing(self):
        self.assertEqual(
            self.sales.mapped("state"),
            ["draft", "draft", "draft", "draft", "draft", "sale"],
        )
        jobs = self.env["queue.job"].search([])
        self.assertEqual(len(jobs), 5)
        for job in jobs[:4]:
            Job.load(self.env, job.uuid).perform()
        self.assertEqual(
            self.sales.mapped("state"),
            ["draft", "sale", "sale", "sale", "sale", "sale"],
        )
        self._close_session()
        self._check_closing_session()

        Job.load(self.env, jobs[0].uuid).perform()
