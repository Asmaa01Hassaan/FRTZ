from odoo import models, fields, api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hide_buttons = fields.Boolean(string=_("Hide Buttons"))
    hide_sale_send_preview_buttons = fields.Boolean(
        string=_("Hide 'Send by Email' & 'Preview' buttons on Sales Orders"),
        config_parameter='sale.hide_send_preview_buttons'
    )

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('account.hide_buttons', self.hide_buttons)
        self.env['ir.config_parameter'].sudo().set_param('sale.hide_send_preview_buttons', self.hide_sale_send_preview_buttons)

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update({
            'hide_buttons': self.env['ir.config_parameter'].sudo().get_param('account.hide_buttons', default=False),
            'hide_sale_send_preview_buttons': self.env['ir.config_parameter'].sudo().get_param('sale.hide_send_preview_buttons', default=False),
        })
        return res

