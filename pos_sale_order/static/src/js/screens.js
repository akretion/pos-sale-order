odoo.define('pos_sale_order.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');

    screens.ReceiptScreenWidget.include({
        // We desactivate the automatic print on js side
        // eslint-disable-next-line no-empty-function
        print: function() {},
    }
    );
})
