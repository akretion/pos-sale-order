# Copyright 2020 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
            "discount": line.discount,
            "product_id": line.product_id.id,
            "id": line.id,
            "pack_lot_ids": [],
        }

    @api.model
    def import_one_pos_order(self, order, draft=False):
        sale_id = order["data"].get("sale_order_id")
        if sale_id:
            self = self.with_context(update_pos_sale_order_id=sale_id)
        return super().import_one_pos_order(order, draft=draft)

    @api.model_create_multi
    def create(self, vals_list):
        pos_sale_order_id = self._context.get("update_pos_sale_order_id")
        if pos_sale_order_id:
            if len(vals_list) == 1:
                sale = self.browse(pos_sale_order_id)
                sale.order_line.unlink()
                sale.write(vals_list[0])
            else:
                raise NotImplementedError
            return sale
        return super().create(vals_list)

    def _pos_json(self):
        data = {
            "sale_order_id": self.id,
            "sale_order_name": self.name,
            "name": self.name,
            "lines": [
                [0, 0, self._prepare_pos_json_line(line)]
                for line in self._get_pos_line()
            ],
            "statement_ids": [],
            "pricelist_id": self.pricelist_id.id,
            "partner_id": self.partner_id.id,
            "partner_name": self.partner_id.name,
            "uid": self.id,
            "sequence_number": 1,
            "creation_date": fields.Datetime.to_string(self.date_order),
            "fiscal_position_id": self.fiscal_position_id.id,
        }
        return {"id": self.id, "data": data}
