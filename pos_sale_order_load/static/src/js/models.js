/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy (https://www.akretion.com)
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("pos_sale_order_load.models", function (require) {
    "use strict";
    var models = require("point_of_sale.models");

    var order_initialize_original = models.Order.prototype.initialize;
    var export_as_JSON_original = models.Order.prototype.export_as_JSON;
    var init_from_JSON_original = models.Order.prototype.init_from_JSON;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.set("sale_order_id", null);
            this.set("only_payment", null);
            this.set("sale_order_name", null);
            return order_initialize_original.call(this, attributes, options);
        },
        init_from_JSON: function (json) {
            var res = init_from_JSON_original.call(this, json);
            this.sale_order_id = json.sale_order_id;
            this.only_payment = json.only_payment;
            this.sale_order_name = json.sale_order_name;
            return res;
        },
        export_as_JSON: function () {
            var res = export_as_JSON_original.call(this);
            var order = this;
            res.sale_order_id = order.sale_order_id;
            res.sale_order_name = order.sale_order_name;
            return res;
        },
    });
});
