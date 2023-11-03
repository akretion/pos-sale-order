odoo.define('pos_sale_order_gift_card.OrderReceipt', function(require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');

    const PSOGCOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            get giftcards() {
                return this.receiptEnv.giftcards;
            }
    }
    Registries.Component.extend(OrderReceipt, PSOGCOrderReceipt);

    return OrderReceipt;
});
