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
        return cls.env["sale.order"].browse(res["ids"])

    @classmethod
    def create_random_uid(cls):
        return "%05d-%03d-%04d" % (randint(1, 99999), randint(1, 999), randint(1, 9999))

    @classmethod
    def _get_pos_data(cls, partner=False, to_invoice=False, amount_return=0):
        payments = None
        if amount_return:
            payments = [(cls.cash_pm, 65 + amount_return)]

        data = cls.create_ui_order_data(
            cls, cls.lines, customer=partner, is_invoiced=to_invoice, payments=payments
        )
        if amount_return:
            data["data"]["amount_return"] = amount_return
        data["data"]["creation_date"] = datetime.now().isoformat()
        return data

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context={"test_partner_mismatch": True})

        # Create product
        cls.product0 = cls.create_product("Product 0", cls.categ_basic, 10.0)
        cls.product1 = cls.create_product("Product 1", cls.categ_basic, 5)
        cls.product2 = cls.create_product("Product 2", cls.categ_basic, 15)

        cls.lines = [
            (cls.product0, 3.0),
            (cls.product1, 1.0),
            (cls.product2, 2.0),
        ]
        cls.config = cls.basic_config
        cls.open_new_session(cls)  # open_new_session is not a class method, hack it
        # cls.lines = [
        #    {
        #        "product_id": cls.env.ref("product.product_product_1").id,
        #        "qty": 3.0,
        #        "price_unit": 10.0,
        #    },
        #    {
        #        "product_id": cls.env.ref("product.product_product_3").id,
        #        "qty": 1.0,
        #        "price_unit": 5.0,
        #    },
        #    {
        #        "product_id": cls.env.ref("product.product_product_5").id,
        #        "qty": 2.0,
        #        "price_unit": 15.0,
        #    },
        # ]

        # Open a session and extract cashregirster

        ##
        # journal_obj = cls.env["account.journal"]
        # cls.check_journal = journal_obj.create({"name": "Check", "type": "bank"})
        # cls.card_journal = journal_obj.create({"name": "Card", "type": "bank"})
        # cls.cash_journal = journal_obj.search([("code", "=", "CSH1")])
        # TODO Gestion des Chèque et CB
        # pay_method_obj = cls.env["pos.payment.method"]
        # cls.check_payment_method = pay_method_obj.create({
        #    "name": "Check",
        #    "is_cash_count": False,
        #    })
        # cls.card_payment_method = pay_method_obj.create({
        #    "name": "Card",
        #    "is_cash_count": False,
        #    })
        # cls.cash_payment_method = pay_method_obj.create({
        #    "name": "Cash",
        #    "is_cash_count": True,
        #    "cash_journal_id": cls.check_journal.id,
        #    })
        # cls.pos.payment_method_ids = (
        #    cls.check_payment_method,
        #    cls.card_payment_method,
        #    cls.cash_payment_method,
        #    )
        # cls.pos.open_session_cb()
        # cls.session = cls.pos.current_session_id
        # cls.cash_statement = cls.session.statement_ids.filtered(
        #    lambda s: s.journal_id.code == "CSH1"
        # )
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_3 = cls.env.ref("base.res_partner_3")
        cls.partner_4 = cls.env.ref("base.res_partner_4")
        cls.partner_anonymous = cls.env.ref("pos_sale_order.res_partner_anonymous")
