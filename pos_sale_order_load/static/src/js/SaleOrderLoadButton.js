/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy (https://www.akretion.com)
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("pos_sale_order_load.SaleOrderLoadButton", function (require) {
    "use strict";
    // Display a link to backend's sale order tree view
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const core = require("web.core");
    const _t = core._t;

    class SaleOrderLoadButton extends PosComponent {
        async onClick() {
            var ret = await this.showPopup("ConfirmPopup", {
                title: _t("Confirm Sale Order Load"),
                body: _t(
                    "Warning, you are going to load and edit an existing order.\n" +
                        "Once saved, the content of the initial order will be lost."
                ),
            });
            if (ret.confirmed) {
                window.open(
                    "/web#view_type=list&amp;model=sale.order&amp;action=pos_sale_order_load.action_select_sale_order_pos",
                    "backoffice"
                );
            }
        }
    }
    SaleOrderLoadButton.template = "SaleOrderLoadButton";

    Registries.Component.add(SaleOrderLoadButton);

    return SaleOrderLoadButton;
});
