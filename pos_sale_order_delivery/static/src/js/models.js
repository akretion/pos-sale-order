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
            this.set("commitment_date", null);
            this.set("warehouse", null);
            return res;
        },
        export_as_JSON: function () {
            var res = export_as_JSON_original.call(this);
            var order = this;
            if (order.get("delivery_when") === "now") {
                res.deliver_now = true;
                res.commitment_date = false;
            } else if (order.get("delivery_when") === "later") {
                res.deliver_now = false;
                res.commitment_date = order.get("commitment_date");
            } else {
                res.deliver_now = false;
                res.commitment_date = false;
            }
            res.warehouse_id = order.get("warehouse_id");
            return res;
        },
    });

    models.load_models([
        {
            model: "stock.warehouse",
            fields: ["name"],
            domain: [],
            loaded: function (self, warehouses) {
                self.warehouses = warehouses.map(function (warehouse) {
                    if (warehouse.id === self.config.warehouse_id[0])
                        warehouse.selected = true;
                    return warehouse;
                });
            },
        },
    ]);
});
