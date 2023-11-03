odoo.define("pos_sale_order.ReceiptScreen", function (require) {
    "use strict";

    const { Printer } = require('point_of_sale.Printer');
    var ReceiptScreen = require("point_of_sale.ReceiptScreen");
    var Registries = require("point_of_sale.Registries");

    var PSOReceiptScreen = (ReceiptScreen) =>
        class PSOReceiptScreen extends ReceiptScreen {
            // copy entire function from odoo
            // because there is no way to inherit it properly
            async _sendReceiptToCustomer() {
                const printer = new Printer(null, this.env.pos);
                const receiptString = this.orderReceipt.comp.el.outerHTML;
                const ticketImage = await printer.htmlToImg(receiptString);
                const order = this.currentOrder;
                const client = order.get_client();
                const orderName = order.get_name();
                const orderClient = { email: this.orderUiState.inputEmail, name: client ? client.name : this.orderUiState.inputEmail };
                const order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
                await this.rpc({
                    // CHANGE: pos.order -> sale.order
                    model: 'sale.order',
                    // END CHANGE
                    method: 'action_receipt_to_customer',
                    args: [[order_server_id], orderName, orderClient, ticketImage],
                });
            }
        };

    Registries.Component.extend(ReceiptScreen, PSOReceiptScreen);
    return PSOReceiptScreen;
});
