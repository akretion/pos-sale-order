import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {formatMonetary} from "@web/views/fields/formatters";
import {Component, onWillRender, toRaw} from "@odoo/owl";

export class PosPaymentDataField extends Component {
    static template = "pos_sale_order.PosPaymentDataField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.formatMonetary = formatMonetary;
        onWillRender(() => this.formatData());
    }

    formatData() {
        const posPaymentData = this.props.record.data[this.props.name];
        this.posPaymentData =
            Object.keys(posPaymentData).length && toRaw(posPaymentData);
    }
}

export const posPaymentDataField = {
    component: PosPaymentDataField,
};

registry.category("fields").add("pos_payment_data_field", posPaymentDataField);
