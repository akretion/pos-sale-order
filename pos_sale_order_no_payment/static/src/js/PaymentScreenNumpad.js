/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_no_payment.PaymentScreenNumpad", function (require) {
    "use strict";

    var PaymentScreenNumpad = require("point_of_sale.PaymentScreenNumpad");
    var Registries = require("point_of_sale.Registries");

    // If payment is dissallowed (like a quotation)
    // remove payment options and bypass validation

    var PSONPPaymentScreenNumpad = (PaymentScreenNumpad) =>
        class PSONPPaymentScreenNumpad extends PaymentScreenNumpad {
            get currentOrder() {
                return this.env.pos.get_order();
            }
        };

    Registries.Component.extend(PaymentScreenNumpad, PSONPPaymentScreenNumpad);
});
