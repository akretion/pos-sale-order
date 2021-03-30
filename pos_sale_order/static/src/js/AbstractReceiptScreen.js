/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy (https://www.akretion.com)
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define("pos_sale_order.AbstractReceiptScreen", function (require) {
    "use strict";

    var AbstractReceiptScreen = require("point_of_sale.AbstractReceiptScreen");
    var Registries = require("point_of_sale.Registries");

    var PSOAbstractReceiptScreen = (AbstractReceiptScreen) =>
        class PSOAbstractReceiptScreen extends AbstractReceiptScreen {
            async _printReceipt() {
                return true;
            }
        };

    Registries.Component.extend(AbstractReceiptScreen, PSOAbstractReceiptScreen);
    return PSOAbstractReceiptScreen;
});
