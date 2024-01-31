# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.tools import float_compare, float_is_zero

from odoo.addons.queue_job.job import Job

from .common import CommonCase


@tagged("-at_install", "post_install")
class GeneralCase(CommonCase):
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
        # we expect 4 payment (one per invoice)
        self.assertEqual(len(move), 4)
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
        moves = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 4 payment (one per invoice)
        self.assertEqual(len(moves), 4)
        # The invoice name is set in payment move ref
        self.assertEqual(
            set(moves.mapped("ref")), set(self.sales.invoice_ids.mapped("name"))
        )
        self.assertEqual(sum(moves.mapped("amount_total")), 390)

    def test_payment_sum_zero(self):
        for sale in self.sales[1:]:
            sale.with_context(
                disable_pos_cancel_warning=True,
                pos_cancel_payment_method_id=self.cash_pm.id,
            ).action_cancel()
            sale.unlink()

        data = self._get_pos_data(
            lines=[
                (self.product0, -3.0),
                (self.product1, -1.0),
                (self.product2, -2.0),
            ]
        )
        sale = self._create_sale([data])
        self._close_session()
        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        self.assertEqual(len(move), 0)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(sale.invoice_ids.amount_total, 0)

    def test_split_transaction_payment(self):
        """Ensure that payment are generated even for no cash payment"""
        # use _write as write is forbidden with open session
        self.cash_pm._write({"split_transactions": True})
        self._close_session()
        moves = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 6 payment (one per sale)
        self.assertEqual(len(moves), 6)
        for move in moves:
            self.assertTrue(move.ref)
            # The move should look like "{sale_order_name} - {invoice_name}"
            sale_name, invoice_name = move.ref.split(" - ")
            self.assertIn(sale_name, self.sales.mapped("name"))
            self.assertIn(invoice_name, self.sales.invoice_ids.mapped("name"))

        self.assertEqual(sum(moves.mapped("amount_total")), 390)

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
        # Check that we have splitted the cash payment
        # We except to have 5 payments line
        # 2 for partner_anonymous (as one payment have been done on a "old sale")
        # 2 for partner 2 (as one invoice have been generated immediately)
        # 1 for partner 3
        self.assertEqual(len(self.pos_session.statement_ids.line_ids), 5)

        # Odoo can create rescue session if we do something wrong
        # Ensure that is not the case
        session = self.env["pos.session"].search([("rescue", "=", True)])
        self.assertFalse(session)

    def test_backoffice_draft_invoice(self):
        sale = self.sales[0]
        sale.action_confirm()
        sale._create_invoices()
        # Do not post the invoice and close the session

        with self.assertRaises(UserError):
            self._close_session()

    def test_backoffice_paid_sale_without_invoice(self):
        # create a backoffice order without payment
        sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner_2.id,
                "order_line": [(0, 0, {"product_id": self.product0.id})],
            }
        )
        sale.action_confirm()

        # Register payment on the sale order
        # The payment is linked to a pos session
        wizard = self.env["pos.payment.wizard"].create_wizard(sale)
        self.assertEqual(
            wizard.available_payment_method_ids, self.config.payment_method_ids
        )
        wizard.payment_method_id = self.cash_pm

        wizard.pay()
        self.assertEqual(len(sale.payment_ids), 1)

        # Close the session and check the invoice linked to the sale order
        with self.assertRaises(UserError):
            self._close_session()

    def test_job(self):
        self.assertEqual(
            self.sales.mapped("state"),
            ["draft", "draft", "draft", "draft", "draft", "sale"],
        )
        jobs = self.env["queue.job"].search(
            [("name", "=", "sale.order.action_job_confirm")]
        )
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
        jobs = self.env["queue.job"].search(
            [("name", "=", "sale.order.action_job_confirm")]
        )
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

    def test_close_session_with_cancelled_orders(self):
        # We cancel an anonymous order and two partner 3 orders
        anonymous_so = self.sales[0]
        partner_3_so = self.sales.filtered(lambda s: s.partner_id == self.partner_3)
        cancelled_so = anonymous_so | partner_3_so
        not_cancelled_so = self.sales - cancelled_so

        for so in cancelled_so:
            rv = so.action_cancel()
            self.assertEqual(rv["type"], "ir.actions.act_window")
            self.assertEqual(rv["res_model"], "pos.sale.order.cancel.wizard")

            rv = so.with_context(
                disable_pos_cancel_warning=True,
                pos_cancel_payment_method_id=self.cash_pm.id,
            ).action_cancel()
            self.assertEqual(rv, True)

        # Each cancelled order should have an invoice and a refund
        # and the to_invoice order should have an invoice
        invoices = self.sales.invoice_ids.filtered(
            lambda invoice: invoice.move_type == "out_invoice"
        )
        refunds = self.sales.invoice_ids.filtered(
            lambda invoice: invoice.move_type == "out_refund"
        )

        self.assertEqual(len(invoices), 4)
        self.assertEqual(len(refunds), 3)

        self._close_session()

        # We should now have the 2 more invoice, one for the anonymous SO
        # and one for the non to_invoice partner 2 SO

        invoices = self.sales.invoice_ids.filtered(
            lambda invoice: invoice.move_type == "out_invoice"
        )
        refunds = self.sales.invoice_ids.filtered(
            lambda invoice: invoice.move_type == "out_refund"
        )
        self.assertEqual(len(invoices), 6)
        self.assertEqual(len(refunds), 3)

        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        self.assertTrue(
            all(
                [
                    float_compare(
                        sol.qty_invoiced,
                        sol.product_uom_qty,
                        precision_digits=precision,
                    )
                    >= 0
                    for sale in not_cancelled_so
                    for sol in sale.order_line
                ]
            ),
            "All the not cancelled sale order lines should be invoiced",
        )

        self.assertTrue(
            all(
                [
                    float_is_zero(
                        sol.qty_invoiced,
                        precision_digits=precision,
                    )
                    for sale in cancelled_so
                    for sol in sale.order_line
                ]
            ),
            "All the cancelled sale order lines should be invoiced and refunded",
        )

        self.assertEquals(
            sum([sale.amount_total for sale in self.sales]),
            sum([invoice.amount_total for invoice in invoices]),
            "All sales should be fully invoiced",
        )

        self.assertEquals(
            sum([sale.amount_total for sale in cancelled_so]),
            sum([invoice.amount_total for invoice in refunds]),
            "All cancelled sales should be fully refunded",
        )

        self.assertEqual(self.pos_session.invoice_ids, self.sales.invoice_ids)
        self.assertEqual(len(self.sales.invoice_ids), 6 + 3)

        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(set(refunds.mapped("state")), {"posted"})

        self.assertEqual(set(invoices.mapped("payment_state")), {"paid", "reversed"})
        # The cancelled orders should have been refunded
        self.assertEqual(set(refunds.mapped("payment_state")), {"paid"})

        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we now have only 3 payments (one per non refunded invoice)
        self.assertEqual(len(move), 3)
        self.assertEqual(sum(move.mapped("amount_total")), 195)

    def test_cancel_order_after_session_close(self):
        # Close session
        self._close_session()
        # Cancel first order of partner 3
        partner_3_so = self.sales.filtered(lambda s: s.partner_id == self.partner_3)[0]
        # We have one invoice one payment
        self.assertEqual(len(partner_3_so.invoice_ids), 1)
        self.assertEqual(len(partner_3_so.payment_ids), 1)

        # Without session, we can't cancel the order
        with self.assertRaisesRegex(UserError, "There is no session opened"):
            partner_3_so.action_cancel()

        # Open a new session
        self.config.open_session_cb(check_coa=False)
        self.pos_session = self.config.current_session_id
        self._create_session_sale(pos_session=self.pos_session)

        # Cancel the order
        rv = partner_3_so.action_cancel()
        self.assertEqual(rv["type"], "ir.actions.act_window")
        self.assertEqual(rv["res_model"], "pos.sale.order.cancel.wizard")

        rv = partner_3_so.with_context(
            disable_pos_cancel_warning=True,
            pos_cancel_payment_method_id=self.cash_pm.id,
        ).action_cancel()
        self.assertEqual(rv, True)

        partner_3_so.action_cancel()

        # We should now have 2 invoices 2 payments for the partner 3 sale order
        self.assertEqual(len(partner_3_so.invoice_ids), 2)
        self.assertEqual(len(partner_3_so.payment_ids), 2)
        self.assertEqual(set(partner_3_so.invoice_ids.mapped("state")), {"posted"})
        # An invoice and a refund
        self.assertEqual(
            set(partner_3_so.invoice_ids.mapped("move_type")),
            {"out_invoice", "out_refund"},
        )

        # Close the current session
        self._close_session()
        # The sale order should still have 2 invoices and 2 payments
        self.assertEqual(len(partner_3_so.invoice_ids), 2)
        self.assertEqual(len(partner_3_so.payment_ids), 2)
        # The refund should have been reconciled
        self.assertEqual(
            set(partner_3_so.invoice_ids.mapped("payment_state")), {"paid"}
        )

    def test_close_session_with_cancelled_orders_with_different_payment_method(self):
        # We cancel an anonymous order with bank payment
        so = self.sales[0]
        rv = so.with_context(
            disable_pos_cancel_warning=True,
            pos_cancel_payment_method_id=self.bank_pm.id,
        ).action_cancel()

        self.assertEqual(rv, True)
        self.assertEqual(len(so.invoice_ids), 2)
        self.assertEqual(
            set(so.invoice_ids.mapped("move_type")),
            {"out_invoice", "out_refund"},
        )
        self._close_session()
        self.assertEqual(len(so.invoice_ids), 2)
        self.assertEqual(
            set(so.invoice_ids.mapped("move_type")),
            {"out_invoice", "out_refund"},
        )
        self.assertEqual(set(so.invoice_ids.mapped("state")), {"posted"})
        # The invoices should have been reconciled anyway
        self.assertEqual(
            set(so.invoice_ids.mapped("payment_state")), {"paid", "reversed"}
        )

    def test_cancel_order_after_session_close_with_different_payment_method(self):
        # Close session
        self._close_session()

        # Open a new session
        self.config.open_session_cb(check_coa=False)
        self.pos_session = self.config.current_session_id
        self._create_session_sale(pos_session=self.pos_session)
        # We cancel an anonymous order with bank payment

        so = self.sales[0]
        rv = so.with_context(
            disable_pos_cancel_warning=True,
            pos_cancel_payment_method_id=self.bank_pm.id,
        ).action_cancel()

        self.assertEqual(rv, True)
        self.assertEqual(len(so.invoice_ids), 2)
        self.assertEqual(
            set(so.invoice_ids.mapped("move_type")),
            {"out_invoice", "out_refund"},
        )
        self._close_session()
        self.assertEqual(len(so.invoice_ids), 2)
        self.assertEqual(
            set(so.invoice_ids.mapped("move_type")),
            {"out_invoice", "out_refund"},
        )
        self.assertEqual(set(so.invoice_ids.mapped("state")), {"posted"})
        # The invoices should have been reconciled anyway
        self.assertEqual(set(so.invoice_ids.mapped("payment_state")), {"paid"})

    def test_reinvoicing(self):
        self._close_session()
        so = self.sales[0]
        self.assertEqual(len(so.invoice_ids), 1)
        self.assertEqual(so.invoice_status, "invoiced")
        self.assertEqual(so.invoice_ids.state, "posted")
        self.assertEqual(so.invoice_ids.payment_state, "paid")
        self.assertEqual(so.invoice_ids.move_type, "out_invoice")
        so.action_reinvoice_pos_order()
        self.assertEqual(len(so.invoice_ids), 3)
        self.assertEqual(so.invoice_status, "invoiced")
        self.assertEqual(set(so.invoice_ids.mapped("state")), {"posted"})
        self.assertEqual(so.invoice_ids[1].move_type, "out_refund")
        self.assertEqual(so.invoice_ids[2].move_type, "out_invoice")
        self.assertEqual(set(so.invoice_ids.mapped("payment_state")), {"paid"})


@tagged("-at_install", "post_install")
class SpecialCase(CommonCase):
    def test_with_refund_sale_and_split_payment(self):
        self.cash_pm.split_transactions = True
        refund_lines = [
            (self.product0, -3.0),
            (self.product1, -1.0),
            (self.product2, -2.0),
        ]
        datas = [
            self._get_pos_data(lines=refund_lines),
            self._get_pos_data(),
            self._get_pos_data(),
        ]
        self._create_sale(datas)
        self._close_session()
        move = self.env["account.move"].search(
            [("journal_id", "=", self.cash_pm.cash_journal_id.id)]
        )
        # we expect 3 payments and all must be reconciled, and reconciled together
        lines = move.line_ids.filtered(
            lambda s: s.account_id == self.cash_pm.receivable_account_id
        )
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(line.reconcile)
        self.assertEqual(len(lines.full_reconcile_id), 1)
