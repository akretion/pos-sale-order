# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ("sale.order", "pos.bus.mixin", "pos.load.mixin")

    _sql_constraints = (
        (
            "pos_reference_uniq",
            "unique (pos_reference, session_id)",
            "The pos_reference must be uniq per session",
        ),
    )

    # Pos order interesting fields
    last_order_preparation_change = fields.Char(
        string="Last preparation change",
        help="Last printed state of the order",
    )
    amount_difference = fields.Monetary(
        string="Difference",
        readonly=True,
    )
    amount_paid = fields.Monetary(
        string="Paid",
    )
    amount_return = fields.Monetary(
        string="Returned",
        readonly=True,
    )
    session_id = fields.Many2one(
        "pos.session",
        string="Session",
        index=True,
        domain="[('state', '=', 'opened')]",
        copy=False,
        readonly=True,
    )
    payment_ids = fields.One2many(
        "pos.payment",
        "pos_sale_order_id",
        string="PoS Payments",
        readonly=True,
    )
    floating_order_name = fields.Char("PoS Order Name")
    pos_reference = fields.Char(
        string="Receipt Number",
        readonly=True,
        copy=False,
        index=True,
    )
    sequence_number = fields.Integer(
        string="PoS Sequence Number",
        help="A session-unique sequence number for the order",
        default=1,
    )
    tracking_number = fields.Char(
        string="PoS Order Number",
        compute="_compute_tracking_number",
    )
    uuid = fields.Char(
        string="Uuid",
        readonly=True,
        copy=False,
    )
    to_invoice = fields.Boolean("To invoice")

    account_move = fields.Many2one(
        "account.move",
        "Invoice",
        compute="_compute_account_move",
    )
    picking_id = fields.Many2one(
        "stock.picking",
        "Picking",
        compute="_compute_picking_id",
    )
    pos_payment_data = fields.Json(compute="_compute_pos_payment_data")

    # Custom pos_sale_order fields
    unit_to_deliver = fields.Integer(
        compute="_compute_unit_to_deliver",
    )
    pos_payment_state = fields.Selection(
        [("none", "Not needed"), ("pending", "Pending Payment"), ("done", "Done")],
        compute="_compute_pos_payment",
        store=True,
    )
    pos_amount_to_pay = fields.Monetary(
        string="POS amount to pay",
        compute="_compute_pos_payment",
        store=True,
    )
    is_invoiced = fields.Boolean(
        "Is Invoiced",
        compute="_compute_is_invoiced",
    )
    email = fields.Char(
        string="Email",
        compute="_compute_contact_details",
        readonly=False,
    )
    mobile = fields.Char(
        string="Mobile",
        compute="_compute_contact_details",
        readonly=False,
    )

    # Original Related fields
    config_id = fields.Many2one(
        "pos.config",
        related="session_id.config_id",
        string="Point of Sale",
        store=True,
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        related="session_id.config_id.picking_type_id",
        readonly=False,
    )
    sale_journal = fields.Many2one(
        "account.journal",
        related="session_id.config_id.journal_id",
        readonly=True,
    )
    order_edit_tracking = fields.Boolean(
        related="config_id.order_edit_tracking",
        readonly=True,
    )
    available_payment_method_ids = fields.Many2many(
        "pos.payment.method",
        related="config_id.payment_method_ids",
        readonly=True,
    )
    session_move_id = fields.Many2one(
        "account.move",
        related="session_id.move_id",
        readonly=True,
    )

    # Mapped fields
    lines = fields.One2many(related="order_line")
    crm_team_id = fields.Many2one(related="team_id", readonly=False)

    # Discarded fields
    pos_order_line_ids = fields.One2many("sale.order.line", store=False)
    margin = fields.Monetary(store=False)
    margin_percent = fields.Float(store=False, digits=(12, 4))
    is_total_cost_computed = fields.Boolean(store=False)
    picking_count = fields.Integer(store=False)
    failed_pickings = fields.Boolean(store=False)
    general_note = fields.Text(store=False)
    nb_print = fields.Integer(store=False)
    shipping_date = fields.Date(store=False)
    is_tipped = fields.Boolean(store=False)
    tip_amount = fields.Monetary(store=False)
    refund_orders_count = fields.Integer(store=False)
    refunded_order_id = fields.Many2one("sale.order", store=False)
    ticket_code = fields.Char(store=False)
    is_edited = fields.Boolean(store=False)
    has_deleted_line = fields.Boolean(store=False)
    # Pos online payment
    online_payment_method_id = fields.Many2one("pos.payment.method", store=False)
    next_online_payment_amount = fields.Float(store=False)
    has_refundable_lines = fields.Boolean(store=False)

    sale_order_count = fields.Integer(compute="_compute_sale_order_count")

    def _link_combo_items(self, combo_child_uuids_by_parent_uuid):
        return

    def add_payment(self, data):
        data = self.env["pos.payment"]._adapt_vals_to_payment(data, "create")
        if data:
            self.env["pos.order"].__class__.add_payment(self, data)

    def _compute_prices(self):
        return self.env["pos.order"].__class__._compute_prices(self)

    def _process_saved_order(self, draft):
        return self.id

    def read_pos_data(self, data, config_id):
        return self.env["pos.order"].__class__.read_pos_data(self, data, config_id)

    @api.model
    def _load_pos_data_fields(self, config_id):
        return self.env["pos.order"]._load_pos_data_fields(config_id)

    @api.model
    def _load_pos_data_domain(self, data):
        return self.env["pos.order"]._load_pos_data_domain(data)

    def get_preparation_change(self):
        return self.env["pos.order"].__class__.get_preparation_change(self)

    def _ensure_to_keep_last_preparation_change(self, vals):
        return self.env["pos.order"].__class__._ensure_to_keep_last_preparation_change(
            self, vals
        )

    def _add_mail_attachment(self, name, ticket, basic_ticket):
        return self.env["pos.order"].__class__._add_mail_attachment(
            self, name, ticket, basic_ticket
        )

    def _prepare_mail_values(self, email, ticket, basic_ticket):
        return self.env["pos.order"].__class__._prepare_mail_values(
            self, email, ticket, basic_ticket
        )

    def action_send_receipt(self, email, ticket_image, basic_image):
        return self.env["pos.order"].__class__.action_send_receipt(
            self, email, ticket_image, basic_image
        )

    def get_ticket_screen_order_data(self):
        return self.env["pos.order"].__class__.get_ticket_screen_order_data(self)

    @api.depends("partner_id")
    def _compute_contact_details(self):
        return self.env["pos.order"].__class__._compute_contact_details(self)

    @api.depends("sequence_number", "session_id")
    def _compute_tracking_number(self):
        return self.env["pos.order"].__class__._compute_tracking_number(self)

    @api.depends("invoice_status")
    def _compute_is_invoiced(self):
        for order in self:
            order.is_invoiced = order.invoice_status == "invoiced"

    @api.depends("amount_total", "payment_ids.amount", "state")
    def _compute_pos_payment(self):
        for record in self:
            if (
                record.state in ("draft", "cancel", "sent")
                or not record.amount_total
                or isinstance(record.id, fields.NewId)
            ):
                record.pos_amount_to_pay = 0
                record.pos_payment_state = "none"
            else:
                residual = record.amount_total - sum(
                    record.mapped("payment_ids.amount")
                )
                record.pos_amount_to_pay = residual
                if float_is_zero(
                    residual, precision_rounding=record.currency_id.rounding
                ):
                    record.pos_payment_state = "done"
                else:
                    record.pos_payment_state = "pending"

    @api.depends("invoice_ids")
    def _compute_account_move(self):
        for record in self:
            record.account_move = fields.first(record.invoice_ids)

    def _compute_picking_id(self):
        for record in self:
            record.picking_id = fields.first(record.picking_ids)

    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = 1

    def _get_lines_to_deliver(self):
        return self.order_line.filtered(lambda s: s.product_id.type != "service")

    @api.depends("order_line.product_uom_qty", "order_line.qty_delivered")
    def _compute_unit_to_deliver(self):
        # be carefull here the qty total is the sum of item
        # this have a meaning for simple case when everything is a unit
        # if it's not a unit then it have no meaning
        # maybe you should adapt this to your case
        for record in self:
            lines = record._get_lines_to_deliver()
            record.unit_to_deliver = sum(lines.mapped("product_uom_qty")) - sum(
                lines.mapped("qty_delivered")
            )

    def _compute_pos_payment_data(self):
        self.pos_payment_data = {}
        for record in self.filtered(lambda so: so.payment_ids):
            record.pos_payment_data = {
                "payments": [
                    {
                        "id": payment.id,
                        "method": payment.payment_method_id.name,
                        "amount": payment.amount,
                        "currency": payment.currency_id.id,
                    }
                    for payment in record.payment_ids
                ],
                "amount_paid": record.amount_paid,
                "amount_difference": record.amount_difference,
            }

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

    def action_pos_order_invoice(self):
        for order in self:
            if order.partner_id == order.session_id.config_id.anonymous_partner_id:
                raise UserError(_("Partner is required if you want an invoice"))
            order.action_confirm()
            order._create_invoices()
            order.invoice_ids.action_post()
        return True

    def _get_receipts(self):
        """Inherit to generate your own ticket"""
        return []

    def _get_valid_session(self, order):
        return self.env["pos.order"]._get_valid_session(order)

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Linked Sale Orders"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.id,
        }
