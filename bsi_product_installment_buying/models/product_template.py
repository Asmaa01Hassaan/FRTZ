# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"
    """
    Here, we have inherited the product.template class and added relavent
    fields that allows user to add installments for a particular product.
    """

    installment_ids = fields.Many2many("installment.config", string="Installment")
    installment_ok = fields.Boolean(string="Installments Allowed")

    @api.constrains("installment_ok")
    def validate_installments(self):
        """
        This function generates a validation error if a user try to save a
        product if installment box is checked but no installment is provided
        """
        for record in self:
            if record.installment_ok is True:
                if not self.installment_ids:
                    raise ValidationError("Atleast one installment should be defined")
