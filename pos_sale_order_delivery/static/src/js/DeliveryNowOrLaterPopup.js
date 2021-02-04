/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("pos_sale_order_delivery.DeliveryNowOrLaterPopUp", function (require) {
    "use strict";
    /* global owl */
    var AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    var {useState} = owl.hooks;
    var Registries = require("point_of_sale.Registries");

    class DeliveryNowOrLaterPopUp extends AbstractAwaitablePopup {
        constructor(parent, props) {
            super(parent, props);
            this.state = useState({
                date: null,
                warehouse: null,
                warehouse_id: null,
                warehouses: this.env.pos.warehouses,
                when: null,
                allow_delivery_now: false,
                allow_delivery_later: false,
                no_delivery_message: false,
                loaded: false,
            });
            this.props.askWarehouse = this.env.pos.config.iface_ask_warehouse;
        }
        mounted() {
            this.fetchDate();
        }
        async getPayload() {
            this.state.warehouse_id = parseInt(this.state.warehouse_id);
            this.state.warehouse = this.state.warehouses.filter((wh) => {
                return wh.id === this.state.warehouse_id;
            })[0];
            return this.state;
        }
        async clickDeliveryLater() {
            this.state.when = "later";
            return this.confirm();
        }
        async clickDeliveryNow() {
            this.state.when = "now";
            return this.confirm();
        }
        async clickNoDelivery() {
            this.state.when = "no";
            return this.confirm();
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        async fetchDate() {
            var payload = this.currentOrder.export_as_JSON();
            this.rpc({
                model: "sale.order",
                method: "compute_pos_requested_date",
                args: [payload],
            }).then((result) => {
                this.state.disabled = false;
                this.state.date = result.date;
                this.state.allow_delivery_now = result.allow_delivery_now;
                this.state.allow_delivery_later = result.allow_delivery_later;
                this.state.no_delivery_message = result.no_delivery_message;
                this.state.loaded = true;
            });
        }
    }
    Registries.Component.add(DeliveryNowOrLaterPopUp);
});
