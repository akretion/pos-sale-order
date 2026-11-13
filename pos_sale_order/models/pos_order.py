# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _adapt_vals_to_sale(self, vals, mode):
        if mode == "create" and not vals.get("partner_id"):
            pos_session = self.env["pos.session"].browse(vals["session_id"])
            vals["partner_id"] = pos_session.config_id.anonymous_partner_id.id

        def adapt(command, method):
            if len(command) == 3 and isinstance(command[2], dict):
                return [
                    command[0],
                    command[1],
                    method(command[2], mode),
                ]
            return command

        if "lines" in vals:
            vals["order_line"] = [
                adapt(command, self.env["pos.order.line"]._adapt_vals_to_sale_line)
                for command in vals.pop("lines")
            ]

        if "payment_ids" in vals:
            vals["payment_ids"] = [
                adapt(command, self.env["pos.payment"]._adapt_vals_to_payment)
                for command in vals.pop("payment_ids")
            ]
        for key in list(vals.keys()):
            if key not in self.env["sale.order"]._fields:
                _logger.warning(
                    "The field %s is not present in sale.order, it will be removed from the vals dict for the %s operation",
                    key,
                    mode,
                )
                del vals[key]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return self.env["sale.order"].create(
            [self._adapt_vals_to_sale(vals, "create") for vals in vals_list]
        )

    def write(self, vals):
        # TODO: Get the checks from super
        return self.env["sale.order"].write(self._adapt_vals_to_sale(vals, "write"))

    def browse(self, ids=()):
        return self.env["sale.order"].browse(ids)

    def read(self, fields=None, load="_classic_read"):
        if fields:
            fields = [field for field in self.env["sale.order"]._fields]
        return self.env["sale.order"].read(fields, load)

    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        if field_names:
            for field in field_names[:]:
                if field not in self.env["sale.order"]._fields:
                    _logger.warning(
                        "The field %s is not present in sale.order, "
                        "it will be removed from the field_names list "
                        "for the search_fetch operation",
                        field,
                    )
                    field_names.remove(field)
        return self.env["sale.order"].search_fetch(
            domain, field_names, offset, limit, order
        )

    def _process_order(self, order, existing_order):
        sale_id = super()._process_order(order, existing_order)
        sale = self.browse(sale_id)
        # native code will print the invoice when state is "paid"
        # this state do not exist on sale order
        if sale.to_invoice:
            sale.action_pos_order_invoice()
        else:
            sale.action_confirm()
        return sale.id

    def _prepare_return_amount_payment(self, pos_order, order, pos_session, draft):
        cash_payment_method = pos_session.payment_method_ids.filtered("is_cash_count")[
            :1
        ]
        if not cash_payment_method:
            raise UserError(
                self.env._(
                    "No cash statement found for this session. "
                    "Unable to record returned cash."
                )
            )
        return {
            "name": self.env._("return"),
            "session_id": pos_session.id,
            "pos_order_id": order.id,
            "amount": -pos_order["amount_return"],
            "payment_date": fields.Datetime.now(),
            "payment_method_id": cash_payment_method.id,
            "is_change": True,
        }

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        pos_order_without_return = pos_order.copy()
        pos_order_without_return["amount_return"] = 0
        super()._process_payment_lines(
            pos_order_without_return, order, pos_session, draft
        )
        prec_acc = order.pricelist_id.currency_id.decimal_places
        if not draft and not float_is_zero(pos_order["amount_return"], prec_acc):
            vals = self._prepare_return_amount_payment(
                pos_order, order, pos_session, draft
            )
            order.add_payment(vals)
