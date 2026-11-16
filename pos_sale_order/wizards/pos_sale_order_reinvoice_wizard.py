# Copyright 2024 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PosSaleOrderReinvoiceWizard(models.TransientModel):
    _name = "pos.sale.order.reinvoice.wizard"
    _description = "PoS Sales Order Reinvoice"

    sale_order_id = fields.Many2one("sale.order", required=True, readonly=True)
    # Required in the form: the wizard is created without a customer, the
    # action checks that one was chosen.
    partner_id = fields.Many2one("res.partner", string="Customer")
    amount_total = fields.Monetary(related="sale_order_id.amount_total", readonly=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id", readonly=True)

    def _get_receivable_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type == "receivable"
        )

    def _get_payment_journal(self):
        """Journal in which the payment of the order was booked.

        The reallocation is bookkept where the payment was: the receivable of
        the two customers is moved between the two documents in the journal of
        the Point of Sale payment.
        """
        self.ensure_one()
        payment = fields.first(self.sale_order_id.payment_ids)
        if not payment or not payment.payment_method_id.cash_journal_id:
            raise UserError(
                _("The payment of the order %s has no journal.")
                % self.sale_order_id.name
            )
        return payment.payment_method_id.cash_journal_id

    def _reallocate_payment(self, refund, invoice):
        """Move the payment of the order from the PoS customer to the new one.

        The refund credits the receivable of the PoS customer and the new
        invoice debits the receivable of the chosen customer: a miscellaneous
        operation moves the balance from one partner to the other, on the same
        receivable account, so that both documents are settled without any
        payment.
        """
        self.ensure_one()
        order = self.sale_order_id
        journal = self._get_payment_journal()
        refund_lines = self._get_receivable_lines(refund)
        invoice_lines = self._get_receivable_lines(invoice)
        amount = -sum(refund_lines.mapped("balance"))
        label = _("PoS reinvoicing of %s") % order.name
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": fields.Date.context_today(self),
                "ref": label,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": refund_lines.account_id.id,
                            "partner_id": refund.commercial_partner_id.id,
                            "name": label,
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": invoice_lines.account_id.id,
                            "partner_id": invoice.commercial_partner_id.id,
                            "name": label,
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        # The partner has to be the same on all the reconciled receivable
        # lines, so the refund and the invoice are reconciled with the line of
        # their own partner.
        for move_lines, partner in (
            (refund_lines, refund.commercial_partner_id),
            (invoice_lines, invoice.commercial_partner_id),
        ):
            operation_line = move.line_ids.filtered(
                lambda line, partner=partner: line.partner_id == partner
            )
            (move_lines | operation_line).reconcile()
        return move

    def action_reinvoice(self):
        self.ensure_one()
        order = self.sale_order_id
        if not self.partner_id:
            raise UserError(_("Please select the customer to reinvoice."))
        if not order.pos_can_be_reinvoiced:
            raise UserError(
                _(
                    "Can’t generate invoice for this order since it has been "
                    "already invoiced or its session is still open."
                )
            )
        # We use a little hack here to force a refund creation
        for line in order.order_line:
            line.qty_to_invoice = -line.qty_invoiced
        # Create the refund, still booked on the customer of the order
        refund = order._create_invoices(final=True)
        refund.action_post()
        # The new invoice is booked on the chosen customer
        order.write(
            {
                "partner_invoice_id": self.partner_id.id,
                "partner_shipping_id": self.partner_id.id,
            }
        )
        invoice = order._create_invoices(final=True)
        invoice.action_post()
        self._reallocate_payment(refund, invoice)
        # Then we display the new invoice
        return {
            "name": _("Created Invoice"),
            "view_mode": "form",
            "res_id": invoice.id,
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": self.env.context,
        }
