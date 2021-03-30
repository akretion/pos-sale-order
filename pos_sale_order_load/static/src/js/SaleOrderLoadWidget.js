/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy (https://www.akretion.com)
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("pos_sale_order_load.SaleOrderLoadWidget", function (require) {
    "use strict";
    // Display a link to backend's sale order tree view
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class SaleOrderLoadWidget extends PosComponent {}
    Registries.Component.add(SaleOrderLoadWidget);
});
