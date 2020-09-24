# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.point_of_sale.models.pos_order import PosOrder

_logger = logging.getLogger(__name__)

# We propagate some PosOrder method to the SaleOrder object
# using monkey-patching to reduce at the maximun the duplicated code
# Then we can inherit it correctly in the sale_order.py file


class SaleOrderPatched(models.Model):
    _inherit = "sale.order"


SaleOrderPatched.create_from_ui = PosOrder.create_from_ui
SaleOrderPatched._process_order = PosOrder._process_order
SaleOrderPatched.add_payment = PosOrder.add_payment
SaleOrderPatched._payment_fields = PosOrder._payment_fields
SaleOrderPatched._prepare_bank_statement_line_payment_values = (
    PosOrder._prepare_bank_statement_line_payment_values
)
SaleOrderPatched._match_payment_to_invoice = PosOrder._match_payment_to_invoice


class SaleOrder(models.Model):
    _inherit = "sale.order"

    _sql_constraints = [
        (
            "pos_reference_uniq",
            "unique (pos_reference, session_id)",
            "The pos_reference must be uniq per session",
        )
    ]

    pos_reference = fields.Char(
        string="Receipt Ref", readonly=True, copy=False, default=""
    )
    session_id = fields.Many2one(
        "pos.session",
        string="Session",
        index=True,
        domain="[('state', '=', 'opened')]",
        states={"draft": [("readonly", False)]},
        copy=False,
        readonly=True,
    )
    statement_ids = fields.One2many(
        "account.bank.statement.line",
        "pos_so_statement_id",
        string="Payments",
        states={"draft": [("readonly", False)]},
        readonly=True,
        copy=False,
    )
    invoice_id = fields.Many2one(
        "account.invoice", "Invoice", compute="_compute_invoice_id"
    )
    picking_id = fields.Many2one(
        "stock.picking", "Picking", compute="_compute_picking_id"
    )

    def _compute_invoice_id(self):
        for record in self:
            record.invoice_id = record.invoice_ids and record.invoice_ids[0]

    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids and record.picking_ids[0]

    def _prepare_pos_line(self, line):
        return {
            "product_id": line["product_id"],
            "product_uom_qty": line["qty"],
            "price_unit": line["price_unit"],
            "tax_id": line["tax_ids"],
        }

    @api.model
    def _order_fields(self, ui_order):
        pos_session = self.env["pos.session"].browse(ui_order["pos_session_id"])
        config = pos_session.config_id
        if not ui_order["partner_id"]:
            partner_id = config.anonymous_partner_id.id
            ui_order["partner_id"] = partner_id
        lines = [(0, 0, self._prepare_pos_line(line[2])) for line in ui_order["lines"]]
        return {
            "user_id": ui_order["user_id"] or False,
            "session_id": ui_order["pos_session_id"],
            "order_line": lines,
            "pos_reference": ui_order["name"],
            "partner_id": ui_order["partner_id"] or False,
            "date_order": ui_order["creation_date"],
            "fiscal_position_id": ui_order["fiscal_position_id"],
            "pricelist_id": ui_order["pricelist_id"],
        }

    def _prepare_bank_statement_line_payment_values(self, data):
        res = super()._prepare_bank_statement_line_payment_values(data)
        res["pos_so_statement_id"] = res.pop("pos_statement_id")
        return res

    def action_pos_order_paid(self):
        """ We do nothing, not needed in sale_order case"""
        return True

    def action_pos_order_invoice(self):
        for order in self:
            if order.partner_id == order.session_id.config_id.anonymous_partner_id:
                raise UserError(_("Partner is required if you want an invoice"))
            order.action_confirm()
            order.action_invoice_create()
            order.invoice_id.action_invoice_open()
        return True

    @api.model
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res["session_id"] = self.session_id.id
        return res

    @api.model
    def create_from_ui(self, orders):
        ids = []
        order_uuid_done = []
        order_uuid_failed = []
        error_message = ""
        for order in orders:
            try:
                with self.env.cr.savepoint():
                    ids += super().create_from_ui([order])
                    order_uuid_done.append(order["id"])
            except Exception as e:
                order_uuid_failed.append(order["id"])
                _logger.error(
                    "Sync POS Order failed order id {} data: {} error: {}".format(
                        order["id"], order, e
                    )
                )
        if order_uuid_failed:
            error_message = _("Fail to sync the following order\n - {}").format(
                "\n - ".join(order_uuid_failed)
            )
        return ids, order_uuid_done, error_message

    def write(self, vals):
        super().write(vals)
        if "partner_invoice_id" in vals:
            for record in self:
                for statement in record.statement_ids:
                    if statement.partner_id != record.partner_invoice_id:
                        statement.partner_id = record.partner_invoice_id
        return True
