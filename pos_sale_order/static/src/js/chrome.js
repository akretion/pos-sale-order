odoo.define('pos_sale_order.chrome', function (require) {
    "use strict";
    var chrome = require('point_of_sale.chrome');
    var PosBaseWidget = require('point_of_sale.BaseWidget');

    var SaleWidget = PosBaseWidget.extend({
        template: 'SaleWidget',
        renderElement: function() {
          this._super();
        }
    });

    chrome.Chrome.include({
        // Put the button in the view
        init: function(parent, options) {
            this.SaleWidget = new SaleWidget(parent, options);
            this._super(parent, options);
        },
        build_widgets: function() {
            this._super();
            this.SaleWidget.insertAfter(this.$('.order-selector'));
        },
    });
 });
