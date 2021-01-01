/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_delivery.ClientOrderRefButton", function (require) {
    "use strict";

    var PosComponent = require("point_of_sale.PosComponent");
    var {useListener} = require("web.custom_hooks");
    var Registries = require("point_of_sale.Registries");

    class DeliveryNowOrLaterButton extends PosComponent {
        constructor(parent, props) {
            super(parent, props);
            useListener("click", this.onClick);
        }
        async onClick() {
            var ret = await this.showPopup("DeliveryNowOrLaterPopUp", {
                warehouses: [],
            });
            if (ret.confirmed) {
                this.peristChoice(ret.payload);
            }
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        peristChoice(payload) {
            var order = this.currentOrder;
            order.set("commitment_date", payload.date);
            order.set("warehouse", payload.warehouse);
            order.set("delivery_when", payload.when);
            this.render();
        }
    }
    Registries.Component.add(DeliveryNowOrLaterButton);
});
