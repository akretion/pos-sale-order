/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_no_payment.QuotationButton", function (require) {
    "use strict";

    var PosComponent = require("point_of_sale.PosComponent");
    var {useListener} = require("web.custom_hooks");
    var Registries = require("point_of_sale.Registries");
    var core = require("web.core");
    var _t = core._t;

    class QuotationButton extends PosComponent {
        constructor(parent, props) {
            super(parent, props);
            useListener("click", this.onClick);
        }
        async onClick() {
            var is_quotation = this.currentOrder.get("is_quotation");
            if (is_quotation) {
                this.currentOrder.set("is_quotation", false);
            } else {
                var ret = await this.showPopup("ConfirmPopup", {
                    title: _t("Confirm Quotation"),
                    body: _t("You will need to confirm the sale in the backend"),
                });
                if (ret.confirmed) {
                    this.currentOrder.set("is_quotation", true);
                }
            }
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
    }
    Registries.Component.add(QuotationButton);
});
