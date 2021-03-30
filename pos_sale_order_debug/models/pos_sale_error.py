# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosSaleError(models.Model):
    _name = "pos.sale.error"
    _description = "Pos Sale Error"

    name = fields.Char()
    pos_config_id = fields.Many2one("pos.config")
    pos_session_id = fields.Many2one("pos.session")
    user_id = fields.Many2one("res.users")
    company_id = fields.Many2one("res.company", related="pos_config_id.company_id")
    data = fields.Serialized()

    def _log_error(self, order):
        name = order["data"].get("name")
        record = self.search([("name", "=", name)])
        session_id = order["data"].get("pos_session_id")
        if session_id:
            session = self.env["pos.session"].browse(session_id)
            session_id = session.exists().id
        vals = {
            "name": name,
            "pos_session_id": session_id,
            "user_id": order["data"].get("user_id"),
            "data": order,
        }
        if record:
            record.write(vals)
        else:
            self.create(vals)

    def run(self):
        sales = self.env["sale.order"]
        for record in self:
            sales |= self.env["sale.order"].import_one_pos_order(record.data)
        return sales
