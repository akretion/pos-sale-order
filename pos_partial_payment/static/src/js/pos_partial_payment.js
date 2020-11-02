/* Copyright 2020 Akretion (https://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define('pos_partial_payment.hijack_model_load', function (require) {
    "use strict";
    var pos_models = require('point_of_sale.models');
    var bankStatementOriginal = null;
    var journalLoadedOriginal = null;
    function bankStatementLoaded(self, cashregisters, tmp){
        self.cashregisters = cashregisters;
        var one = cashregisters[0];
        var copy = Object.assign({}, one);
        copy.name = 'Pay later';
        copy.account_id = [-1, "Fake account"];
        copy.journal_id = [-1, "Pay later"];
        self.cashregisters.push(copy);
        bankStatementOriginal(self, cashregisters, tmp);
    }

    function journalLoaded(self, journals){
        self.journals = journals;
        var one = journals[0];
        var copy = Object.assign({}, one);
        copy.id = -1;
        self.journals.push(copy);
        journalLoadedOriginal(self, journals);
    }

    pos_models.PosModel.prototype.models.forEach(function (m) {
        if (m.model === "account.journal") {
            journalLoadedOriginal = m.loaded
            m.loaded = journalLoaded
        } else if (m.model === "account.bank.statement") {
            bankStatementOriginal = m.loaded
            m.loaded = bankStatementLoaded
        }
    });
});
