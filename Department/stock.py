# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import osv, fields

class Stock_out(osv.osv):
    _inherit = 'stock.picking.out'
    def _prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
        if not context:
            context = {}
        res = super(Stock_out, self)._prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=context)
        if picking.sale_id.department_id:
            res['department_id'] = picking.sale_id.department_id
        return res
    
Stock_out()

class Stock_in(osv.osv):
    _inherit = 'stock.picking.in'
    def _prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
        if not context:
            context = {}
        res = super(Stock_in, self)._prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=context)
        if picking.purchase_id.department_id:
            res['department_id'] = picking.purchase_id.department_id
        return res
    
Stock_in()

class account(osv.osv):
    _inherit = 'account.move.line'
    def _prepare_analytic_line(self, cr, uid, obj_line, context=None):
        if not context:
            context = {}
        res = super(account, self)._prepare_analytic_line(cr, uid, obj_line, context)
        if obj_line.invoice:
            if obj_line.invoice.department_id.id:
                res['department_id'] = obj_line.invoice.department_id.id
        return res
   
