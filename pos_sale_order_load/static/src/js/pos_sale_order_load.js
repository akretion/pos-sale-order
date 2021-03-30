/* Copyright (C) 2020-Today Akretion (https://www.akretion.com)
    @author Raphaël Reverdy (https://www.akretion.com)
    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/
/* global posmodel */
/* eslint-disable no-alert */

odoo.define("pos_sale_order_load.pos_sale_order_load", function (require) {
    "use strict";
    var models = require("point_of_sale.models");
    var tools = require("pos_backend_communication.tools");
    var core = require("web.core");
    var _t = core._t;
    var {posbus} = require("point_of_sale.utils");

    function set_so(message) {
        var data = message.data;
        var json = data.payload.data;
        // Add the customer to list of customers
        // mandatory if used with pos_backend_partner
        var partner = {id: json.partner_id, name: json.partner_name, country_id: []};
        posmodel.db.add_partners([partner]);

        // Ensure uuid unicity (no duplicates)
        var uuid = json.uid;
        var order = null;
        var already_loaded = posmodel.get_order_list().some(function (o) {
            if (o.uid === uuid) {
                order = o;
                return true;
            }
            return false;
        });
        if (already_loaded) {
            console.log("order already loaded");
        } else {
            order = new models.Order(
                {},
                {
                    pos: posmodel,
                    json: json,
                }
            );
            order.sequence_number = posmodel.pos_session.sequence_number++;
            posmodel.get("orders").add(order);
        }
        posmodel.set_order(order);
        // Force reprint of ticket btn (# of orders)
        posbus.trigger("order-deleted");
        // Try to get the focus back
        alert(_t("SO Loaded"));
    }
    tools.callbacks["sale_order.sale_selected"] = set_so;
});
