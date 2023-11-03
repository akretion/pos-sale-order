odoo.define("pos_sale_order_gift_card.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            order_super.initialize.apply(this, arguments);
            this.bought_gift_cards = [];
        },
        get_bought_giftcards(){
            return this.bought_gift_cards;
        },
        getOrderReceiptEnv: function() {
            var res = order_super.getOrderReceiptEnv.apply(this, arguments);
            res["giftcards"] = this.get_bought_giftcards();
            return res;
        },
    });

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _after_orders_received: function(res) {
            posmodel_super._after_orders_received.apply(this, arguments);
            var self = this;
            res.orders.forEach(function (order) {
                if (order.pos_reference.endsWith(" " + self.get_order().uid)) {
                    self.get_order().bought_gift_cards = order.bought_gift_cards;
                }
            });
        }
    });

});
