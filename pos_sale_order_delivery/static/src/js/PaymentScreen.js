odoo.define("pos_sale_order_delivery.PaymentScreen", function (require) {
    "use strict";

    var PaymentScreen = require("point_of_sale.PaymentScreen");
    var Registries = require("point_of_sale.Registries");

    var PSODPaymentScreen = (PaymentScreen) =>
        class PSODPaymentScreen extends PaymentScreen {
            async _isOrderValid(isForceValidate) {
                var res = super._isOrderValid(isForceValidate);
                var delivery_set = this.currentOrder.get("delivery_when");
                if (!delivery_set) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("No delivery set"),
                        body: this.env._t("The delivery should be set"),
                    });
                    return false;
                }
                return res;
            }
        };
    PaymentScreen.template = "PaymentScreen";

    Registries.Component.extend(PaymentScreen, PSODPaymentScreen);

    return PaymentScreen;
});
