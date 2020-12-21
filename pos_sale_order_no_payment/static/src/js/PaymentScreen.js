/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_no_payment.PaymentScreen", function (require) {
    "use strict";

    var PaymentScreen = require("point_of_sale.PaymentScreen");
    var Registries = require("point_of_sale.Registries");
    var models = require("point_of_sale.models");
    var NumberBuffer = require("point_of_sale.NumberBuffer");

    // If payment is dissallowed (like a quotation)
    // remove payment options and bypass validation

    var PSONPPaymentScreen = (PaymentScreen) =>
        class PSONPPaymentScreen extends PaymentScreen {
            async _onNewOrder(newOrder) {
                newOrder.on("change", this.actOnPayment, this);
                // Trigger manually first
                this.actOnPayment();
                return super._onNewOrder(newOrder);
            }
            actOnPayment() {
                if (this.currentOrder.is_payment_allowed()) {
                    this.activatePayment();
                } else {
                    this.deactivatePayment();
                }
            }
            activatePayment() {
                this.currentOrder.is_paid = models.Order.prototype.is_paid;
                this.togglePayment(true);
            }
            deactivatePayment() {
                this.currentOrder.is_paid = function () {
                    return true;
                };
                this.togglePayment(false);
                // Remove all paymentlines
                this.currentOrder
                    .get_paymentlines()
                    .forEach((line) => this.currentOrder.remove_paymentline(line));

                this.currentOrder.set_to_invoice(false);

                NumberBuffer.reset();
                this.render();
            }
        };
    Registries.Component.extend(PaymentScreen, PSONPPaymentScreen);
});
