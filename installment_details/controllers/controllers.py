# -*- coding: utf-8 -*-
# from odoo import http


# class InstallmentDetails(http.Controller):
#     @http.route('/installment_details/installment_details', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/installment_details/installment_details/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('installment_details.listing', {
#             'root': '/installment_details/installment_details',
#             'objects': http.request.env['installment_details.installment_details'].search([]),
#         })

#     @http.route('/installment_details/installment_details/objects/<model("installment_details.installment_details"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('installment_details.object', {
#             'object': obj
#         })

