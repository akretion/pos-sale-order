// Copyright 2024 Akretion (http://www.akretion.com).
// @author Florian Mounier <florian.mounier@akretion.com>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("pos_sale_order_optional_receipt.PrintReceiptToggleButton", function (
    require
) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const {useListener} = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");

    class PrintReceiptToggleButton extends PosComponent {
        constructor(parent, props) {
            super(parent, props);
            useListener("click", this.onClick);
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        async onClick() {
            const order = this.currentOrder;
            order.set("no_receipt", !order.get("no_receipt"));
            this.render();
        }
    }
    Registries.Component.add(PrintReceiptToggleButton);
});
