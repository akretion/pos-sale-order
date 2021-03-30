/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_no_payment.models", function (require) {
    "use strict";

    // If payment is dissallowed (like a quotation)
    // remove payment options and bypass validation

    var models = require("point_of_sale.models");

    models.PosModel.prototype.models.some(function (model) {
        if (model.model !== "product.pricelist") {
            return false;
        }
        model.fields.push("pos_allow_payment");
        return true; // Exit early the iteration of this.models
    });

    var order_initialize_original = models.Order.prototype.initialize;
    var export_as_JSON_original = models.Order.prototype.export_as_JSON;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var res = order_initialize_original.call(this, attributes, options);
            this.set("is_quotation", null);
            return res;
        },
        export_as_JSON: function () {
            var res = export_as_JSON_original.call(this);
            var order = this;
            res.is_quotation = order.get("is_quotation");
            return res;
        },
    });

    models.Order = models.Order.extend({
        is_payment_allowed: function () {
            // Our core function
            var order = this;
            var pricelist = order.pricelist;
            var is_quote = order.get("is_quotation");
            if (is_quote) {
                // Never accept payment on quotation
                return false;
            }
            return pricelist.pos_allow_payment;
        },
    });
});
