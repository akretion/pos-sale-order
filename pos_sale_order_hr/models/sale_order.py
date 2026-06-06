# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.pos_hr.models.pos_order import PosOrder


class SaleOrderPatched(models.Model):
    _inherit = "sale.order"


SaleOrderPatched._compute_cashier = PosOrder._compute_cashier


class SaleOrder(models.Model):
    _inherit = "sale.order"

    employee_id = fields.Many2one(
        "hr.employee",
        help="Person who uses the cash register."
        "It can be a reliever, a student or an interim employee.",
        states={"done": [("readonly", True)], "invoiced": [("readonly", True)]},
    )
    cashier = fields.Char(string="Cashier", compute="_compute_cashier", store=True)

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super()._order_fields(ui_order)
        order_fields["employee_id"] = ui_order.get("employee_id")
        return order_fields

    def _export_for_ui(self, order):
        result = super()._export_for_ui(order)
        result.update(
            {
                "employee_id": order.employee_id.id,
            }
        )
        return result

    def _get_fields_for_draft_order(self):
        fields = super()._get_fields_for_draft_order()
        fields.append("employee_id")
        return fields
