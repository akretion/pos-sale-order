/* global posmodel _t */
/* eslint-disable no-alert */

odoo.define('pos_sale_order_load.pos_sale_order_load', function (require) {
    "use strict";
    var tools = require('pos_backend_communication.tools');
    var chrome = require('point_of_sale.chrome');
    var models = require('point_of_sale.models');
    var PosBaseWidget = require('point_of_sale.BaseWidget');

    function set_so(message) {
        var data = message.data;
        var json = data.payload.data;
        // Add the customer to list of customers
        // mandatory if used with pos_backend_partner
        var partner = {id: json.partner_id, name: json.partner_name, country_id: [] };
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
            console.log('order already loaded');
        } else {
            order = new models.Order({},{
                    pos:  posmodel,
                    json: json,
            });
            order.sequence_number = posmodel.pos_session.sequence_number++;
            posmodel.get('orders').add(order);
        }

        posmodel.set('selectedOrder', order);
        // Try to get the focus back
        alert(_t('SO Loaded'));
    }
    tools.callbacks['sale_order.sale_selected'] = set_so;

    var SaleOrderLoadWidget = PosBaseWidget.extend({
        template: 'SaleOrderLoadWidget',
        renderElement: function() {
          this._super();
        }
    });

    chrome.Chrome.include({
        // Put the button in the view
        init: function(parent, options) {
            this.SaleOrderLoadWidget = new SaleOrderLoadWidget(parent, options);
            this._super(parent, options);
        },
        build_widgets: function() {
            this._super();
            this.SaleOrderLoadWidget.insertBefore(this.$('.order-selector'));
        },
    });

    var order_initialize_original = models.Order.prototype.initialize;
    var export_as_JSON_original = models.Order.prototype.export_as_JSON;
    var init_from_JSON_original = models.Order.prototype.init_from_JSON;
    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            this.set('sale_order_id', null);
            this.set('only_payment', null);
            return order_initialize_original.call(this, attributes, options);
        },
        init_from_JSON: function(json) {
            var res = init_from_JSON_original.call(this, json);
            this.sale_order_id = json.sale_order_id;
            this.only_payment = json.only_payment;
            return res;
        },
        export_as_JSON: function() {
            var res = export_as_JSON_original.call(this);
            var order = this;
            res.sale_order_id = order.sale_order_id;
            res.only_payment = order.only_payment;
            return res;
        },
    });


 });
