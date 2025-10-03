# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date


class InstallmentConfiguration(models.Model):
    _name = "installment.config"
    _description = "Installment Configuration"
    """
    Here, we have defined installment.config class that allows user to add
    installment details when the installment configuration menuitem is opened.
    """
    name = fields.Char(string="Installments", compute="dynamic_name")
    months = fields.Integer(string="Installment Months", required=True)
    emi = fields.Float(string="EMI extra cost in percentage", required=True)

    def dynamic_name(self):
        """
        This function generates the dynamic name for installment based on
        number of months and emi provided
        """
        for record in self:
            name = ""
            if record.months:
                name = str(record.emi) + "%" + " for " + str(record.months) + " month"
            record.name = name
