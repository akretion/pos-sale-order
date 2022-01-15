# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import api, fields, models


class PosSaleError(models.Model):
    _name = "pos.sale.error"
    _description = "Pos Sale Error"

    name = fields.Char(readonly=True)
    pos_config_id = fields.Many2one(
        "pos.config", related="pos_session_id.config_id", store=True
    )
    pos_session_id = fields.Many2one(
        "pos.session", domain="[('config_id.company_id', '=', company_id)]"
    )
    user_id = fields.Many2one("res.users", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    data = fields.Serialized()
    data_display = fields.Text(compute="_compute_data_display")
    order_id = fields.Many2one("sale.order", readonly=True, string="Sale Order")
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        default="pending",
        required=True,
    )
    error = fields.Text()

    @api.depends("data")
    def _compute_data_display(self):
        for rec in self:
            rec.data_display = json.dumps(rec.data, sort_keys=True, indent=4)

    def _prepare_vals(self, order, exception):
        session_id = order["data"].get("pos_session_id")
        vals = {
            "name": order["data"].get("name"),
            "user_id": order["data"].get("user_id"),
            "data": order,
            "error": str(exception),
        }
        session = self.env["pos.session"].browse(session_id)
        if session.exists():
            vals["pos_session_id"] = session.id
            vals["company_id"] = session.company_id.id
        else:
            vals["company_id"] = self.env.company.id
        return vals

    def _log_error(self, order, exception):
        vals = self._prepare_vals(order, exception)
        record = self.search([("name", "=", vals["name"])])
        if record:
            record.write(vals)
            return record
        else:
            return self.create(vals)

    def run(self):
        for record in self:
            data = record.data
            if record.pos_session_id:
                # give the possibility to use the session from the record
                data["data"]["pos_session_id"] = record.pos_session_id.id
            record.order_id = (
                self.env["sale.order"]
                .with_user(record.user_id)
                .with_company(record.company_id)
                .import_one_pos_order(data)
            )
            if record.order_id:
                record.state = "done"
        return True
