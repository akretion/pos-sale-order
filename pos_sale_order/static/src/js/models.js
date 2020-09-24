odoo.define('pos_sale_order.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var session = require('web.session');

    models.Order = models.Order.extend({
        generate_unique_id: function() {
            return uuidv4();
        },
    },
    );

    models.PosModel = models.PosModel.extend({
        // Redifine the method save_to_server
        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                var result = $.Deferred();
                result.resolve([]);
                return result;
            }

            options = options || {};

            var self = this;
            var timeout = typeof options.timeout === 'number' ? options.timeout : 7500 * orders.length;

            // Keep the order ids that are about to be sent to the
            // backend. In between create_from_ui and the success callback
            // new orders may have been added to it.
            var order_ids_to_sync = _.pluck(orders, 'id');

            // We try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var args = [_.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                })];
            return rpc.query({
                    model: 'sale.order',
                    method: 'create_from_ui',
                    args: args,
                    kwargs: {context: session.user_context},
                }, {
                    timeout: timeout,
                    shadow: !options.to_invoice
                })
                .then(function (server_ids) {
                    _.each(order_ids_to_sync, function (order_id) {
                        self.db.remove_order(order_id);
                    });
                    self.set('failed',false);
                    return server_ids;
                }).fail(function (type, error){
                    // Business Logic Error, not a connection problem
                    if(error.code === 200 ){
                        // If warning do not need to display traceback!!
                        if (error.data.exception_type === 'warning') {
                            delete error.data.debug;
                        }

                        // Hide error if already shown before ...
                        if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                            self.gui.show_popup('error-traceback',{
                                'title': error.data.message,
                                'body':  error.data.debug
                            });
                        }
                        self.set('failed',error);
                    }
                    console.error('Failed to send orders:', orders);
                });
        },
    },
    );
})
