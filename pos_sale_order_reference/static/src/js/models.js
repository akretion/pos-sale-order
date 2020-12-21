/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_reference.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var order_initialize_original = models.Order.prototype.initialize;
    var export_as_JSON_original = models.Order.prototype.export_as_JSON;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var res = order_initialize_original.call(this, attributes, options);
            this.set("client_order_ref", null);
            return res;
        },
        export_as_JSON: function () {
            var res = export_as_JSON_original.call(this);
            var order = this;
            res.client_order_ref = order.get("client_order_ref");
            return res;
        },
    });
});
