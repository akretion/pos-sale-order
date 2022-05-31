# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import CommonCase


@tagged("-at_install", "post_install")
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
        expected = [
            {
                "product_id": product.id,
                "qty": qty,
                "price_unit": product.lst_price,
            }
            for product, qty in self.lines
        ]

        self.assertEqual(res, expected)
        self.assertEqual(sale.amount_total, 65)
        self.assertEqual(len(sale.payment_ids), 1)
        self.assertEqual(sale.payment_ids.amount, 65)

    def test_create_existing_sale(self):
        data = self._get_pos_data()
        sales = self._create_sale([data])
        self.assertEqual(len(sales), 1)

        # trying to push the same data should return the sale previously created
        new_sales = self._create_sale([data])
        self.assertEqual(new_sales, sales)

    def test_create_sale_with_return_amount(self):
        data = self._get_pos_data(amount_return=5)
        sale = self._create_sale([data])
        self.assertEqual(len(sale.payment_ids), 2)
        self.assertEqual(sale.payment_ids[0].amount, 70)
        self.assertEqual(sale.payment_ids[1].amount, -5)

    def test_create_sale_with_invoice(self):
        partner = self.env.ref("base.res_partner_2")
        data = self._get_pos_data(partner=partner, to_invoice=True)
        sale = self._create_sale([data])
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(invoice.amount_total, 65)
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        self.assertEqual(invoice.partner_id, partner)
        self.assertEqual(invoice.state, "posted")

    def test_create_sale_with_discount(self):
        data = self._get_pos_data()
        data["data"]["lines"][0][2]["discount"] = 20
        sale = self._create_sale([data])
        self.assertEqual(sale.order_line[0].discount, 20)
