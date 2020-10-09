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

    var LoadSaleOrderWidget = PosBaseWidget.extend({
        template: 'LoadSaleOrderWidget',
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
            this.loadSaleOrderWidget = new LoadSaleOrderWidget(parent, options);
            this._super(parent, options);
        },
        build_widgets: function() {
            this._super();
            this.loadSaleOrderWidget.insertBefore(this.$('.order-selector'));
        },
    });


 });
