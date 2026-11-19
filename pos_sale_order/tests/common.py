# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import datetime
from random import randint

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


class CommonCase(TestPoSCommon):
    @classmethod
    def _create_sale(cls, data):
        res = cls.env["sale.order"].create_from_ui(data)
        return cls.env["sale.order"].browse([order["id"] for order in res["orders"]])

    @classmethod
    def create_random_uid(cls):
        return "%05d-%03d-%04d" % (randint(1, 99999), randint(1, 999), randint(1, 9999))

    @classmethod
    def _get_pos_data(
        cls,
        pos_session=None,
        partner=False,
        to_invoice=False,
        amount_return=0,
        payments=None,
        lines=None,
    ):
        if payments and amount_return:
            raise NotImplementedError

        if amount_return:
            payments = [(cls.cash_pm, 65 + amount_return)]
        if lines is None:
            lines = cls.lines
        data = cls.create_ui_order_data(
            cls, lines, customer=partner, is_invoiced=to_invoice, payments=payments
        )
        if pos_session:
            data["data"]["pos_session_id"] = pos_session.id
        if amount_return:
            data["data"]["amount_return"] = amount_return
        data["data"]["creation_date"] = datetime.now().isoformat()[0:23] + "Z"
        return data

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        ctx = {"test_partner_mismatch": True}
        cls.env = cls.env(context=ctx)

        # Create product
        cls.product0 = cls.create_product("Product 0", cls.categ_basic, 10.0)
        cls.product1 = cls.create_product("Product 1", cls.categ_basic, 5)
        cls.product2 = cls.create_product("Product 2", cls.categ_basic, 15)

        cls.lines = [
            (cls.product0, 3.0),
            (cls.product1, 1.0),
            (cls.product2, 2.0),
        ]
        cash = cls.basic_config.payment_method_ids.filtered(
            lambda pm: pm.is_cash_count and not pm.split_transactions
        )[:1]
        cash.receivable_account_id = cls.env["account.account"].search(
            [
                ("name", "=", "Account Receivable"),
                ("company_id", "=", cls.company.id),
            ]
        )
        bank = cls.basic_config.payment_method_ids.filtered(
            lambda pm: not pm.is_cash_count and not pm.split_transactions
        )[:1]
        bank.receivable_account_id = cls.env["account.account"].search(
            [
                ("name", "=", "Account Receivable"),
                ("company_id", "=", cls.company.id),
            ]
        )
        # Bank payment method should have a cash journal in pos sale order
        bank.cash_journal_id = cls.company_data["default_journal_bank"]

        cls.config = cls.basic_config.with_context(**ctx)
        cls.open_new_session(cls)  # open_new_session is not a class method, hack it
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_3 = cls.env.ref("base.res_partner_3")
        cls.partner_4 = cls.env.ref("base.res_partner_4")
        cls.partner_anonymous = cls.env.ref("pos_sale_order.res_partner_anonymous")

    def _close_session(self):
        self.pos_session.cash_register_id.balance_end_real = (
            self.pos_session.cash_register_id.balance_start
            + self.pos_session.total_payments_amount
        )
        self.pos_session.action_pos_session_validate()
