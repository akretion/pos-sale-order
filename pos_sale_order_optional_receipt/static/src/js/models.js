// Copyright 2024 Akretion (http://www.akretion.com).
// @author Florian Mounier <florian.mounier@akretion.com>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("pos_sale_order_optional_receipt.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var order_initialize_original = models.Order.prototype.initialize;
    var export_as_JSON_original = models.Order.prototype.export_as_JSON;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var res = order_initialize_original.call(this, attributes, options);
            this.set("no_receipt", false);
            return res;
        },
        export_as_JSON: function () {
            var res = export_as_JSON_original.call(this);
            var order = this;
            res.no_receipt = order.get("no_receipt");
            return res;
        },
    });
});
