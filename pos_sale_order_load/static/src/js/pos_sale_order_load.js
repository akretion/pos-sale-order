'use strict';

odoo.define('pos_sale_order_load.pos_sale_order_load', function (require) {
    var tools = require('pos_backend_communication.tools');
    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var models = require('point_of_sale.models');
    var translation = require('web.translation');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var session = require('web.session');
    var action_url;
    function open_backend(message) {
        action_url = action_url || session.rpc(
            '/web/action/load', { "action_id":"pos_sale_order_load.action_select_sale_order_pos"})
            .then(function (e) { return e.id; });

        action_url.then(function (action_id) {
            var url = "/web#view_type=list&model=sale.order&action=" + action_id;
            var msg = {'type': 'sale_order.choose'};
            tools.open_page(url, msg, 'sale_order');
        });
    }

    function set_so(message)  {
        var data = message.data;
        var json = data.payload.data;
        var order = new models.Order({},{
                pos:  posmodel, // it's a global
                json: json,
        });
        posmodel.get('orders').add(order);
        posmodel.set('selectedOrder', order);

        alert(_t('SO Loaded')); //try to get the focus back
    }
    tools.callbacks['sale_order.sale_selected'] = set_so;

    var SaleOrderLoadWidget = PosBaseWidget.extend({
        template: 'SaleOrderLoadWidget',
        renderElement: function() {
          var self = this;
          this._super();
          this.$('.load-so').click(function(){
              open_backend();
          });
        }
    });


    chrome.Chrome.include({
        //put the button in the view
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
            res['sale_order_id'] = order.sale_order_id;
            res['only_payment'] = order.only_payment;
            return res;
        },
    });


 });
