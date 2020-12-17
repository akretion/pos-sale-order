# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from .common import CommonCase


class TestClosingSession(CommonCase):
    @classmethod
    def _create_session_sale(cls):
        datas = [
            cls._get_pos_data(),
            cls._get_pos_data(amount_return=5),
            cls._get_pos_data(partner=cls.partner_3),
            cls._get_pos_data(partner=cls.partner_3),
            cls._get_pos_data(partner=cls.partner_2),
            cls._get_pos_data(partner=cls.partner_2, to_invoice=True),
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

        self.pos_session.action_pos_session_validate()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.mapped("order_line.invoice_lines.invoice_id")
        self.assertEqual(self.pos_session.invoice_ids, invoices)
        self.assertEqual(len(invoices), 4)

        self._check_invoice_number(
            invoices,
            [(self.partner_2, 2), (self.partner_3, 1), (self.partner_anonymous, 1)],
        )

        self.assertEqual(set(invoices.mapped("state")), {"paid"})

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
        self.pos_session.action_pos_session_validate()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.mapped("order_line.invoice_lines.invoice_id")
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

        self.assertEqual(set(invoices.mapped("state")), {"paid"})

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
        invoice_ids = sale.action_invoice_create()
        invoices = self.env["account.invoice"].browse(invoice_ids)
        invoices.action_invoice_open()

        self.pos_session.action_pos_session_validate()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.mapped("order_line.invoice_lines.invoice_id")
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

        self.assertEqual(set(invoices.mapped("state")), {"paid"})

    def test_backoffice_invoice_and_change_partner_and_close(self):
        # We expect 5 invoices
        # - one invoice for anonymous SO
        # - one for the partner 4
        # - one for the partner 3
        # - two for the partner 2

        sale = self.sales[0]
        sale.action_confirm()
        invoice_ids = sale.action_invoice_create()
        invoices = self.env["account.invoice"].browse(invoice_ids)
        invoices.write({"partner_id": self.partner_4.id})
        invoices.action_invoice_open()

        self.pos_session.action_pos_session_validate()

        self.assertEqual(set(self.sales.mapped("invoice_status")), {"invoiced"})

        invoices = self.sales.mapped("order_line.invoice_lines.invoice_id")
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

        self.assertEqual(set(invoices.mapped("state")), {"paid"})

    def test_backoffice_payment_sale_order(self):
        # create an order without payment
        data = self._get_pos_data()
        data["data"]["statement_ids"] = []
        sale = self._create_sale([data])
        self.pos_session.action_pos_session_validate()
        self.pos.refresh()

        # Open a new session
        self.pos.open_session_cb()
        self._create_session_sale()

        # Register a backoffice payment on sale order
        wizard = self.env["pos.payment.wizard"].create_wizard(sale)
        self.assertEqual(wizard.available_journal_ids, self.pos.journal_ids)
        wizard.journal_id = self.cash_journal

        wizard.pay()
        self.assertEqual(len(sale.statement_ids), 1)

        # Close the session and check the invoice linked to the sale order
        self.pos.current_session_id.action_pos_session_validate()
        self.assertEqual(sale.invoice_ids.state, "paid")
