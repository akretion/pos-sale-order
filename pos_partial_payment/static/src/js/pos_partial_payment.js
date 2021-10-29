/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_partial_payment.hijack_model_load", function (require) {
    "use strict";
    var pos_models = require("point_of_sale.models");
    var posPaymentMethodLoadedOriginal = null;
    var posConfigLoadedOriginal = null;
    var core = require("web.core");
    var _t = core._t;

    function posPaymentMethodLoaded(self, payment_methods) {
        var fake_method = {
            id: -1,
            is_cash_count: false,
            name: _t("Pay later"),
            use_payment_terminal: false,
        };
        payment_methods.push(fake_method);
        posPaymentMethodLoadedOriginal(self, payment_methods);
        // Self.payment_methods is sorted by cash then id.
        // so our negative id is put too high in the list
        // we want our fake payment method to be at the end
        var idx = self.payment_methods.indexOf(fake_method);
        // Remove it where it is
        self.payment_methods.splice(idx, 1);
        // Add it back at the end
        self.payment_methods.push(fake_method);
    }

    function posConfigLoaded(self, configs) {
        posConfigLoadedOriginal(self, configs);
        for (var i = 0; i < configs.length; i++) {
            configs[i].payment_method_ids.push(-1);
        }
    }

    pos_models.PosModel.prototype.models.forEach(function (m) {
        if (m.model === "pos.payment.method") {
            posPaymentMethodLoadedOriginal = m.loaded;
            m.loaded = posPaymentMethodLoaded;
        } else if (m.model === "pos.config") {
            posConfigLoadedOriginal = m.loaded;
            m.loaded = posConfigLoaded;
        }
    });
});
