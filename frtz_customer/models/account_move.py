# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    customer_guarantees_ids = fields.Many2many(
        'res.partner',
        'account_move_customer_guarantees_rel',
        'account_move_id',
        'partner_id',
        string='Customer Guarantees',
        help='Select customers who will act as guarantees for this invoice'
    )
