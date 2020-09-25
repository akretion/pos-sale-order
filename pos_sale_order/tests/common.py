# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import uuid

from odoo import fields
from odoo.tests import SavepointCase


def now():
    return fields.Datetime.to_string(fields.Datetime.now())


class CommonCase(SavepointCase):
    @classmethod
    def _get_pos_line(cls):
        res = []
        for line in cls.lines:
            res.append(
                [
                    0,
                    0,
                    {
                        # "price_subtotal_incl": 1.2,
                        "price_unit": line["price_unit"],
                        # "price_subtotal": 1.2,
                        # "id": 7,
                        "product_id": line["product_id"],
                        "tax_ids": [[6, 0, []]],
                        # "discount": 0,
                        # "pack_lot_ids": [],
                        "qty": line["qty"],
                    },
                ]
            )
        amount = sum([line["qty"] * line["price_unit"] for line in cls.lines])
        return res, amount

    @classmethod
    def _get_payment(cls, amount):
        return [
            [
                0,
                0,
                {
                    "amount": amount,
                    "statement_id": cls.cash_statement.id,
                    "account_id": cls.cash_statement.account_id.id,
                    "name": now(),
                    "journal_id": cls.cash_statement.journal_id.id,
                },
            ]
        ]

    @classmethod
    def _get_pos_data(
        cls, to_invoice=False, partner_id=None, pricelist_id=None, amount_return=0
    ):

        if not pricelist_id:
            pricelist_id = cls.pos.pricelist_id.id

        lines, amount = cls._get_pos_line()
        amount_paid = amount
        if amount_return:
            amount_paid += amount_return

        payments = cls._get_payment(amount_paid)

        # commented key are send by the pos but ignored by this module
        # so I comment them to track what we ignore
        sale_uuid = str(uuid.uuid4())
        return {
            "to_invoice": to_invoice,
            "data": {
                "sequence_number": 2,
                "amount_tax": 0,  # not used
                # "name": "Order 00001-001-0002",
                "name": sale_uuid,
                "uid": sale_uuid,
                "amount_paid": amount_paid,
                "statement_ids": payments,
                "fiscal_position_id": False,
                "partner_id": partner_id,
                "to_invoice": to_invoice,
                "pricelist_id": pricelist_id,
                "lines": lines,
                "amount_return": amount_return,
                "amount_total": amount,
                "creation_date": now(),
                "pos_session_id": cls.session.id,
                "user_id": cls.session.user_id.id,
            },
            "id": sale_uuid,
        }

    @classmethod
    def _create_sale(cls, data):
        res = cls.env["sale.order"].create_from_ui(data)
        return cls.env["sale.order"].browse(res["ids"])

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={"test_partner_mismatch": True})

        # Open a session and extract cashregirster
        cls.pos = cls.env.ref("point_of_sale.pos_config_main")
        cls.pos.warehouse_id = cls.env.ref("stock.warehouse0")
        cls.pos.open_session_cb()
        cls.session = cls.pos.current_session_id
        cls.cash_statement = cls.session.statement_ids.filtered(
            lambda s: s.journal_id.code == "CSH1"
        )
        cls.lines = [
            {
                "product_id": cls.env.ref("product.product_product_1").id,
                "qty": 3.0,
                "price_unit": 10.0,
            },
            {
                "product_id": cls.env.ref("product.product_product_3").id,
                "qty": 1.0,
                "price_unit": 5.0,
            },
            {
                "product_id": cls.env.ref("product.product_product_5").id,
                "qty": 2.0,
                "price_unit": 15.0,
            },
        ]
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_3 = cls.env.ref("base.res_partner_3")
        cls.partner_4 = cls.env.ref("base.res_partner_4")
        cls.partner_anonymous = cls.env.ref("pos_sale_order.res_partner_anonymous")
