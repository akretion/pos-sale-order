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
SaleOrderPatched._get_valid_session = PosOrder._get_valid_session
SaleOrderPatched._process_payment_lines = PosOrder._process_payment_lines


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
    payment_ids = fields.One2many(
        "pos.payment",
        "pos_sale_order_id",
        string="Payments",
        readonly=True,
    )
    to_invoice = fields.Boolean("To invoice")
    account_move = fields.Many2one(
        "account.move", "Invoice", compute="_compute_account_move"
    )
    picking_id = fields.Many2one(
        "stock.picking", "Picking", compute="_compute_picking_id"
    )
    unit_to_deliver = fields.Integer(compute="_compute_unit_to_deliver")
    pos_payment_state = fields.Selection(
        [("none", "Not needed"), ("pending", "Pending Payment"), ("done", "Done")],
        compute="_compute_pos_payment",
        store=True,
    )
    pos_amount_to_pay = fields.Monetary(
        string="POS amount to pay", compute="_compute_pos_payment", store=True
    )
    amount_paid = fields.Float(
        string="Paid",
        states={"draft": [("readonly", False)]},
        readonly=True,
        digits=0,
        default=0,
    )
    is_invoiced = fields.Boolean("Is Invoiced", compute="_compute_is_invoiced")

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super()._payment_fields(order, ui_paymentline)
        res["session_id"] = order.session_id.id
        return res

    @property
    def lines(self):
        return self.order_line

    @api.depends("account_move")
    def _compute_is_invoiced(self):
        for order in self:
            order.is_invoiced = bool(order.account_move)

    @api.depends("amount_total", "payment_ids.amount", "state")
    def _compute_pos_payment(self):
        for record in self:
            if record.state in ("draft", "cancel", "sent") or not record.amount_total:
                record.pos_amount_to_pay = 0
                record.pos_payment_state = "none"
            else:
                residual = record.amount_total - sum(
                    record.mapped("payment_ids.amount")
                )
                record.pos_amount_to_pay = residual
                if residual == 0:
                    record.pos_payment_state = "done"
                else:
                    record.pos_payment_state = "pending"

    @api.depends("invoice_ids")
    def _compute_account_move(self):
        for record in self:
            record.account_move = fields.first(record.invoice_ids)

    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids and record.picking_ids[0]

    @api.depends("order_line.product_uom_qty", "order_line.qty_delivered")
    def _compute_unit_to_deliver(self):
        # be carefull here the qty total is the sum of item
        # this have a meaning for simple case when everything is a unit
        # if it's not a unit then it have no meaning
        # maybe you should adapt this to your case
        for record in self:
            lines = record.order_line.filtered(lambda s: s.product_id.type != "service")
            record.unit_to_deliver = sum(lines.mapped("product_uom_qty")) - sum(
                lines.mapped("qty_delivered")
            )

    def open_pos_payment_wizard(self):
        self.ensure_one()
        wizard = self.env["pos.payment.wizard"].create_wizard(self)
        action = wizard.get_formview_action()
        action["target"] = "new"
        return action

    def open_pos_delivery_wizard(self):
        self.ensure_one()
        wizard = self.env["pos.delivery.wizard"].create_wizard(self)
        action = wizard.get_formview_action()
        action["target"] = "new"
        return action

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
            # date order same implementation as odoo
            "date_order": ui_order["creation_date"].replace("T", " ")[:19],
            "fiscal_position_id": ui_order["fiscal_position_id"],
            "pricelist_id": ui_order["pricelist_id"],
            "to_invoice": ui_order.get("to_invoice"),
            "invoice_policy": "order",
        }

    def add_payment(self, data):
        data["pos_sale_order_id"] = data.pop("pos_order_id")
        return super().add_payment(data)

    def action_pos_order_paid(self):
        """ We do nothing, not needed in sale_order case"""
        return True

    def action_pos_order_invoice(self):
        for order in self:
            if order.partner_id == order.session_id.config_id.anonymous_partner_id:
                raise UserError(_("Partner is required if you want an invoice"))
            order.action_confirm()
            order._create_invoices()
            order.invoice_ids.action_post()
        return True

    @api.model
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res["session_id"] = self.session_id.id
        return res

    def _build_pos_error_message(self, failed):
        return _("Fail to sync the following order\n - {}").format(
            "\n - ".join([str(order["id"]) for order in failed])
        )

    def _get_receipts(self):
        """Inherit to generate your own ticket"""
        return []

    def _process_order(self, order, draft, existing_order):
        sale_id = super()._process_order(order, draft, existing_order)
        sale = self.browse(sale_id)
        # native code will print the invoice when state is "paid"
        # this state do not exist on sale order
        if sale.to_invoice:
            sale.action_pos_order_invoice()
        sale._confirm_pos_order(order)
        return sale.id

    def _confirm_pos_order(self, order):
        return self.with_delay().action_confirm()

    @api.model
    def create_from_ui(self, orders, draft=False):
        result = {"ids": [], "uuids": [], "receipts": [], "error": False}
        failed = []
        for order in orders:
            try:
                with self.env.cr.savepoint():
                    sale = self.search([("pos_reference", "=", order["data"]["name"])])
                    if not sale:
                        sale_id = self._process_order(order, draft, None)
                        sale = self.browse(sale_id)
                    # For update support, see pos_sale_order_load
                    result["ids"] += sale.ids
                    result["receipts"] += sale._get_receipts()
                    result["uuids"].append(order["id"])
            except Exception as e:
                failed.append(order)
                _logger.error(
                    "Sync POS Order failed order id {} data: {} error: {}".format(
                        order["id"], order, e
                    )
                )
        if failed:
            result["error"] = self._build_pos_error_message(failed)
        return result

    def _create_order_picking(self):
        return True
