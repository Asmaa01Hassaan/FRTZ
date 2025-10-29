/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    async setup() {
        super.setup();
        this._hideButtonsIfNeeded();
    },

    async _hideButtonsIfNeeded() {
        if (this.model.root.resModel === 'sale.order') {
            const record = this.model.root;
            if (record.data && record.data.hide_buttons_setting) {
                // Hide buttons immediately when form loads
                this._hideSaleOrderButtons();
            }
        }
    },

    _hideSaleOrderButtons() {
        // Hide Send by Email buttons
        const sendButtons = document.querySelectorAll('button[name="action_quotation_send"]');
        sendButtons.forEach(button => {
            button.style.display = 'none';
        });

        // Hide Preview button
        const previewButton = document.querySelector('button[name="action_preview_sale_order"]');
        if (previewButton) {
            previewButton.style.display = 'none';
        }

        // Hide specific button IDs
        const primarySendButton = document.querySelector('#send_by_email_primary');
        if (primarySendButton) {
            primarySendButton.style.display = 'none';
        }

        const secondarySendButton = document.querySelector('#send_by_email');
        if (secondarySendButton) {
            secondarySendButton.style.display = 'none';
        }
    },

    async onRecordSaved(record) {
        super.onRecordSaved(record);
        if (record.resModel === 'sale.order' && record.data.hide_buttons_setting) {
            this._hideSaleOrderButtons();
        }
    }
});
