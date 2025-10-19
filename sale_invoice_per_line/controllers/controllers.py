# -*- coding: utf-8 -*-
# from odoo import http


# class SaleInvoicePerLine(http.Controller):
#     @http.route('/sale_invoice_per_line/sale_invoice_per_line', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_invoice_per_line/sale_invoice_per_line/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_invoice_per_line.listing', {
#             'root': '/sale_invoice_per_line/sale_invoice_per_line',
#             'objects': http.request.env['sale_invoice_per_line.sale_invoice_per_line'].search([]),
#         })

#     @http.route('/sale_invoice_per_line/sale_invoice_per_line/objects/<model("sale_invoice_per_line.sale_invoice_per_line"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_invoice_per_line.object', {
#             'object': obj
#         })

