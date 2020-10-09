# Copyright 2020 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def select_in_pos_current_order(self):
        """
        Action called from view with self.id = a res.partner.
        """
        return {
            "type": "ir.actions.tell_pos",
            "params": {
                "type": "sale_order.sale_selected",
                "so_id": self.id,
                "payload": self._pos_json(),
            },
        }

    def _get_pos_line(self):
        return self.order_line

    def _prepare_pos_json_line(self, line):
        return {
            "qty": line.product_uom_qty,
            "price_unit": line.price_unit,
            "price_subtotal": line.price_subtotal,
            "price_subtotal_incl": line.price_total,
            "discount": line.discount,
            "product_id": line.product_id.id,
            "tax_ids": [[6, False, line.tax_id.ids]],
            "id": line.id,
            "pack_lot_ids": [],
        }

    #            "config": {
    #                "selected_options": [
    #                    {
    #                        "id": "1",
    #                        "product_id": "4",
    #                        "description": "Poche",
    #                        "quantity": 2,
    #                        "price": 1,
    #                        "notes": "fdsfdfsfds",
    #                    }

    @api.model
    def create_from_ui(self, orders):
        sale_id = orders[0]["data"].get("sale_order_id")
        if sale_id:
            self = self.with_context(update_pos_sale_order_id=sale_id)
        return super().create_from_ui(orders)

    @api.model_create_multi
    def create(self, vals):
        pos_sale_order_id = self._context("update_pos_sale_order_id")
        if pos_sale_order_id:
            sale = self.browse(pos_sale_order_id)
            sale.write(vals)
            return sale
        return super().create(vals)

    def _pos_json(self):
        data = {
            "sale_order_id": self.id,
            "name": "Order {}".format(self.pos_reference),
            "amount_paid": 0,
            "amount_total": self.amount_total,
            "amount_tax": self.amount_tax,
            "amount_return": 0,
            "lines": [
                (0, 0, self._prepare_pos_json_line(line))
                for line in self._get_pos_line()
            ],
            "statement_ids": [],
            # "pos_session_id": 1,
            "pricelist_id": self.pricelist_id.id,
            "partner_id": self.partner_id.id,
            # "user_id": 2,
            "uid": self.pos_reference,
            "sequence_number": 1,
            # "creation_date": "2020-10-08T14:42:42.290Z",
            "fiscal_position_id": self.fiscal_position_id.id,
            "to_invoice": False,
        }
        return {"id": self.pos_reference, "data": data}
