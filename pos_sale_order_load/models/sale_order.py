# Copyright 2020 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def select_in_pos_current_order(self):
        """
        Action called from view with self.id = a res.partner.
        """
        return {
            'type': 'ir.actions.tell_pos',
            'params': {
                'type': 'sale_order.sale_selected',
                'so_id': self.id,
                'payload': self._pos_json(),
            },
        }

    def _pos_json(self):
        false = False
        JSON = {
            "id": "00001-022-0008",
            "data": {
                "name": "Order 00001-022-0008",
                "amount_paid": 0,
                "amount_total": 53.6,
                "amount_tax": 0.6,
                "amount_return": 0,
                "lines": [
                    [0, 0, {
                        "qty": 50,
                        "price_unit": 1,
                        "price_subtotal": 50,
                        "price_subtotal_incl": 50,
                        "discount": 0,
                        "product_id": 1,
                        "tax_ids": [
                            [6, false, []]
                        ],
                        "id": 19,
                        "pack_lot_ids": []
                    }],
                    [0, 0, {
                        "qty": 1,
                        "price_unit": 3,
                        "price_subtotal": 3,
                        "price_subtotal_incl": 3.6,
                        "discount": 0,
                        "product_id": 3,
                        "tax_ids": [
                            [6, false, [1]]
                        ],
                        "id": 21,
                        "pack_lot_ids": [],
                        "config": {
                            "selected_options": [{
                                "id": "1",
                                "product_id": "4",
                                "description": "Poche",
                                "quantity": 2,
                                "price": 1,
                                "notes": "fdsfdfsfds"
                            }]
                        }
                    }]
                ],
                "statement_ids": [],
                "pos_session_id": 1,
                "pricelist_id": 1,
                "partner_id": false,
                "user_id": 2,
                "uid": "00001-022-0008",
                "sequence_number": 8,
                "creation_date": "2020-10-08T14:42:42.290Z",
                "fiscal_position_id": false,
                "to_invoice": false
            }
        }
        return JSON
