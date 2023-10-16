# Copyright 2020 Akretion (https://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import CommonCase


@tagged("-at_install", "post_install")
class TestCashRounding(CommonCase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.config.cash_rounding = True
        cls.config.only_round_cash_method = True
        cls.config.rounding_method = cls.env["account.cash.rounding"].create(
            {
                "name": "Rounding line",
                "rounding": 0.05,
                "strategy": "add_invoice_line",
                "profit_account_id": cls.company[
                    "default_cash_difference_income_account_id"
                ]
                .copy()
                .id,
                "loss_account_id": cls.company[
                    "default_cash_difference_expense_account_id"
                ]
                .copy()
                .id,
                "rounding_method": "HALF-UP",
            }
        )

        cls.rounding_product = cls.create_product(
            "Rounding Product", cls.categ_basic, 10.01
        )

        cls.partner = cls.env.ref("base.res_partner_2")

    def test_cash_rounding_paid_in_cash(self):
        data = self._get_pos_data(
            partner=self.partner,
            to_invoice=True,
            payments=[
                (self.cash_pm, 10),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 10)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(
            invoice.invoice_line_ids.filtered(
                lambda line: line.name == "Rounding line"
            ).account_id.name,
            "Cash Difference Loss (copy)",
        )
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, "posted")

    def test_cash_rounding_paid_in_bank(self):
        data = self._get_pos_data(
            partner=self.partner,
            to_invoice=True,
            payments=[
                (self.bank_pm, 10.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 10.01)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, "posted")

    def test_cash_rounding_paid_in_bank_all_rounding(self):
        self.config.only_round_cash_method = False
        data = self._get_pos_data(
            partner=self.partner,
            to_invoice=True,
            payments=[
                (self.bank_pm, 10),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 10)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(
            invoice.invoice_line_ids.filtered(
                lambda line: line.name == "Rounding line"
            ).account_id.name,
            "Cash Difference Loss (copy)",
        )
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, "posted")

    def test_cash_rounding_paid_in_bank_then_cash(self):
        data = self._get_pos_data(
            partner=self.partner,
            to_invoice=True,
            payments=[
                (self.bank_pm, 5),
                (self.cash_pm, 5),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 10)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(
            invoice.invoice_line_ids.filtered(
                lambda line: line.name == "Rounding line"
            ).account_id.name,
            "Cash Difference Loss (copy)",
        )
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, "posted")

    def test_cash_rounding_paid_in_cash_then_bank(self):
        data = self._get_pos_data(
            partner=self.partner,
            to_invoice=True,
            payments=[
                (self.cash_pm, 5),
                (self.bank_pm, 5.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 10.01)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, "posted")

    def test_cash_rounding_in_grouped_invoices_no_rounding(self):
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.cash_pm, 2),
                (self.bank_pm, 8.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale1 = self._create_sale([data])
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.cash_pm, 2),
                (self.cash_pm, 2),
                (self.cash_pm, 4),
                (self.bank_pm, 2.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale2 = self._create_sale([data])
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 4),
                (self.cash_pm, 3),
                (self.bank_pm, 3.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale3 = self._create_sale([data])
        # Rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 3.01),
                (self.bank_pm, 1),
                (self.bank_pm, 6),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale4 = self._create_sale([data])
        self.env["sale.order"].browse(
            [sale1.id, sale2.id, sale3.id, sale4.id]
        )._create_invoices()
        self.assertEqual(sale1.invoice_ids, sale2.invoice_ids)
        self.assertEqual(sale1.invoice_ids, sale3.invoice_ids)
        self.assertEqual(sale1.invoice_ids, sale4.invoice_ids)

        self.assertEqual(len(sale1.invoice_ids), 1)
        invoice = sale1.invoice_ids

        self.assertEqual(invoice.amount_total, 40.04)
        self.assertEqual(len(invoice.invoice_line_ids), 4)
        self.assertEqual(invoice.partner_id, self.partner)

    def test_cash_rounding_in_grouped_invoices_same_rounding(self):
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 8),
                (self.cash_pm, 2),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale1 = self._create_sale([data])
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 2),
                (self.cash_pm, 2),
                (self.cash_pm, 2),
                (self.cash_pm, 4),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale2 = self._create_sale([data])
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 4),
                (self.bank_pm, 3),
                (self.cash_pm, 3),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale3 = self._create_sale([data])
        # Rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.cash_pm, 3),
                (self.cash_pm, 1),
                (self.cash_pm, 6),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale4 = self._create_sale([data])
        self.env["sale.order"].browse(
            [sale1.id, sale2.id, sale3.id, sale4.id]
        )._create_invoices()
        self.assertEqual(sale1.invoice_ids, sale2.invoice_ids)
        self.assertEqual(sale1.invoice_ids, sale3.invoice_ids)
        self.assertEqual(sale1.invoice_ids, sale4.invoice_ids)

        self.assertEqual(len(sale1.invoice_ids), 1)
        invoice = sale1.invoice_ids

        self.assertEqual(invoice.amount_total, 40)
        self.assertEqual(len(invoice.invoice_line_ids), 8)
        rounding_lines = invoice.invoice_line_ids.filtered(
            lambda line: line.name == "Rounding line"
        )
        for rounding_line in rounding_lines:
            self.assertEqual(
                rounding_line.account_id.name, "Cash Difference Loss (copy)"
            )

        self.assertEqual(invoice.partner_id, self.partner)

    def test_cash_rounding_in_grouped_invoices_various_rounding(self):
        # No rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.cash_pm, 5),
                (self.bank_pm, 5.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale1 = self._create_sale([data])
        # Rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 5),
                (self.cash_pm, 5),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale2 = self._create_sale([data])
        # No rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.bank_pm, 10.01),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale3 = self._create_sale([data])
        # Rounding
        data = self._get_pos_data(
            partner=self.partner,
            payments=[
                (self.cash_pm, 10),
            ],
            lines=[(self.rounding_product, 1)],
        )
        sale4 = self._create_sale([data])

        self.env["sale.order"].browse(
            [sale1.id, sale2.id, sale3.id, sale4.id]
        )._create_invoices()
        self.assertEqual(sale1.invoice_ids, sale3.invoice_ids)
        self.assertEqual(sale2.invoice_ids, sale4.invoice_ids)

        self.assertEqual(len(sale1.invoice_ids), 1)
        invoice = sale1.invoice_ids
        self.assertEqual(invoice.amount_total, 40.02)
        self.assertEqual(len(invoice.invoice_line_ids), 6)
        self.assertEqual(invoice.partner_id, self.partner)
