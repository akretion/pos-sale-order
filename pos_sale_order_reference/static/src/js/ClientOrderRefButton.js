/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_reference.ClientOrderRefButton", function (require) {
    "use strict";

    var PosComponent = require("point_of_sale.PosComponent");
    var {useListener} = require("web.custom_hooks");
    var Registries = require("point_of_sale.Registries");
    var core = require("web.core");
    var _t = core._t;

    class ClientOrderRefButton extends PosComponent {
        constructor(parent, props) {
            super(parent, props);
            useListener("click", this.onClick);
        }
        async onClick() {
            var ret = await this.showPopup("TextInputPopup", {
                title: _t("Order Reference"),
                startingValue: this.currentOrder.get("client_order_ref"),
            });
            if (ret.confirmed) {
                this.currentOrder.set("client_order_ref", ret.payload);
            }
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
    }
    Registries.Component.add(ClientOrderRefButton);
});
