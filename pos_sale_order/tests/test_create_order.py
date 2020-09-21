# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import CommonCase


class TestCreateOrder(CommonCase):
    def test_create_sale(self):
        data = self._get_pos_data()
        sales = self._create_sale([data])
        self.assertEqual(len(sales), 1)
        sale = sales[0]
        self.assertEqual(len(sale.order_line), 3)
        res = [
            {
                "product_id": line.product_id.id,
                "qty": line.product_uom_qty,
                "price_unit": line.price_unit,
            }
            for line in sale.order_line
        ]
        self.assertEqual(res, self.lines)
        self.assertEqual(sale.amount_total, 65)
        self.assertEqual(len(sale.statement_ids), 1)
        self.assertEqual(sale.statement_ids.amount, 65)

    def test_create_existing_sale(self):
        data = self._get_pos_data()
        self._create_sale([data])
        sales = self._create_sale([data])
        self.assertEqual(len(sales), 0)

    def test_create_sale_with_return_amount(self):
        data = self._get_pos_data(amount_return=5)
        sale = self._create_sale([data])
        self.assertEqual(len(sale.statement_ids), 2)
        self.assertEqual(sale.statement_ids[0].amount, -5)
        self.assertEqual(sale.statement_ids[1].amount, 70)

    def test_create_sale_with_invoice(self):
        partner = self.env.ref("base.res_partner_2")
        data = self._get_pos_data(to_invoice=True, partner_id=partner.id)
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 65)
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        self.assertEqual(invoice.partner_id, partner)
        self.assertEqual(invoice.state, "open")
