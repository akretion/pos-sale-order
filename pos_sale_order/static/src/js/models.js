odoo.define("pos_sale_order.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.Order = models.Order.extend({
        generate_unique_id: function () {
            // eslint-disable-next-line no-undef
            return uuidv4();
        },
    });

    models.PosModel = models.PosModel.extend({
        // Redefine the method save_to_server
        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                return Promise.resolve([]);
            }
            // eslint-disable-next-line no-param-reassign
            options = options || {};
            var self = this;
            var timeout =
                typeof options.timeout === "number"
                    ? options.timeout
                    : 30000 * orders.length;

            // We try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var args = [
                _.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                }),
            ];
            return this.rpc(
                {
                    model: "sale.order",
                    method: "create_from_ui",
                    args: args,
                    kwargs: {context: this.session.user_context},
                },
                {
                    timeout: timeout,
                    shadow: !options.to_invoice,
                }
            )
                .then(async function (res) {
                    // Only remove from local storage order that have been sync sucessfully
                    res.uuids.forEach(function (order_id) {
                        self.db.remove_order(order_id);
                    });
                    if (self.proxy.printer !== undefined) {
                        if (typeof self.proxy.printer.print_receipts === "function") {
                            await self.proxy.printer.print_receipts(res.receipts);
                        } else {
                            await Promise.all(
                                res.receipts.map(function (receipt) {
                                    return self.proxy.printer.print_receipt(receipt);
                                })
                            );
                        }
                    }
                    if (res.error) {
                        return Promise.reject({
                            code: 200,
                            message: "Error",
                            debug: res.error,
                        });
                    }
                    self.set("failed", false);
                    return res.orders;
                })
                .catch(function (reason) {
                    var error = reason.message;
                    console.warn("Failed to send orders:", orders);
                    if (error.code === 200) {
                        // Business Logic Error, not a connection problem
                        // Hide error if already shown before ...
                        if (
                            (!self.get("failed") || options.show_error) &&
                            !options.to_invoice
                        ) {
                            self.set("failed", error);
                            throw error;
                        }
                    }
                    throw error;
                });
        },
    });
});
