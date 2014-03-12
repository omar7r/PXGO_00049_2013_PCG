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
#############################################################################
from osv import osv, fields
import time
from datetime import datetime, date


class work_order_other_services(osv.osv):
    _name = 'work.order.other.services'
    _columns = {
            'code':fields.char('Codigo', size=64, required=False, readonly=False),
            'quantity': fields.float('Cantidad'),
            'product_id':fields.many2one('product.product', 'producto ', required=True),
            'work_order_id':fields.many2one('work.order', 'orden de trabajo', required=False),
            'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, select="1"),
                    }
work_order_other_services()
class work_order_time_report(osv.osv):

    def _get_total(self, cr , uid, ids, field_name, args=None, context=None):
        result = {}
        work_order_times = self.pool.get('work.order.time.report').browse(cr, uid, ids, context)
        for work_order_time in work_order_times:
            total = 0.0
            precio_por_defecto = work_order_time.employee_id.product_id.standard_price
            total += work_order_time.horas_normal * precio_por_defecto
            total += work_order_time.horas_nocturnas * (work_order_time.employee_id.producto_hora_nocturna_id.standard_price or precio_por_defecto)
            total += work_order_time.horas_festivas * (work_order_time.employee_id.producto_hora_festiva_id.standard_price or precio_por_defecto)
            result[work_order_time.id] = total
        return result

    _name = "work.order.time.report"
    _columns = {
            'date': fields.date('Fecha'),
            'horas_normal': fields.float('Horas normales'),
            'horas_nocturnas': fields.float('Horas nocturnas'),
            'horas_festivas': fields.float('Horas festivas'),
            'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, select="1"),
            'work_order_id':fields.many2one('work.order', 'orden de trabajo', required=False),
            'total': fields.function(_get_total, method=True, type='float', string='Total', store=False),
                    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S')
    }
work_order_time_report()

class work_order(osv.osv):

    def _get_planta(self, cr , uid, ids, field_name, args=None, context=None):
        result = {}
        work_orders = self.pool.get('work.order').browse(cr, uid, ids, context)
        for work_order in work_orders:
            result[work_order.id] = work_order.element_ids[0].planta
        return result

    def _get_contrata(self, cr , uid, ids, field_name, args=None, context=None):
        result = {}
        work_orders = self.pool.get('work.order').browse(cr, uid, ids, context)
        for work_order in work_orders:
            result[work_order.id] = ""
            for purchase in work_order.purchase_ids:
                result[work_order.id] += purchase.partner_id.display_name + ", "
            result[work_order.id]=result[work_order.id][:-2]
        return result

    def _get_grupo(self, cr, uid, ids, field_name, args=None, context=None):
        result = {}
        usuario = self.pool.get('res.users').browse(cr, uid, uid, context)
        data_obj = self.pool.get('ir.model.data')
        group_id = data_obj.get_object_reference(cr, uid, 'maintenance', "group_maintenance_manager")[1]
        group = self.pool.get('res.groups').browse(cr, uid, group_id, context)
        for work_id in ids:
            result[work_id] = False
            if usuario in group.users:
                result[work_id] = True
        return result

    def _get_element_list(self, cr, uid, ids, field_name, args=None, context=None):
        result = {}
        work_orders = self.pool.get('work.order').browse(cr, uid, ids, context)
        for work_order in work_orders:
            result[work_order.id] = ""
            for element in work_order.element_ids:
                result[work_order.id]+=element.nombre_sin_planta + "\n"
        return result

    def _get_total_other_service(self, cr, uid, ids, field_name, args=None, context=None):
        result = {}
        work_orders = self.pool.get('work.order').browse(cr, uid, ids, context)
        for work_order in work_orders:
            result[work_order.id] = 0
            for service in work_order.other_service_ids:
                result[work_order.id]+=service.quantity*service.product_id.standard_price
        return result


    def _get_total_servicios(self, cr, uid, ids, field_name, args=None, context=None):
        result = {}
        tipo = field_name=="total_servicios_externos"
        work_orders = self.pool.get('work.order').browse(cr, uid, ids, context)
        for work_order in work_orders:
            result[work_order.id] = 0
            for service in work_order.other_service_ids:
                if service.employee_id.externo == tipo:
                    result[work_order.id]+=service.quantity*service.product_id.standard_price

            for hora in work_order.horas_ids:
                if hora.employee_id.externo == tipo:
                    result[work_order.id]+=hora.total
        return result

    _name = 'work.order'
    _inherit = ['mail.thread']
    _columns = {
            'company_id': fields.many2one('res.company', 'Company', required=True, select=1, states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)]}),
            'name':fields.char('Nombre', size=64, required=True),
            'request_id':fields.many2one('intervention.request', 'Solicitud origen', required=False),
            'element_ids':fields.many2many('maintenance.element', 'maintenanceelement_workorder_rel', 'order_id', 'element_id', 'Equipos', required=True),
            'descripcion': fields.text('Descripción'),
            'fecha': fields.date('Fecha de solicitud'),
            'fecha_inicio': fields.datetime('fecha de inicio'),
            'assigned_department_id':fields.many2one('hr.department', 'Departamento asignado', required=False),
            'origin_department_id':fields.many2one('hr.department', 'Departamento origen', required=False),
            'stock_moves_ids':fields.one2many('stock.move', 'work_order_id', 'movimientos asociados', required=False),
            'horas_ids':fields.one2many('work.order.time.report', 'work_order_id', 'Reporte de horas', required=False),
            'other_service_ids':fields.one2many('work.order.other.services', 'work_order_id', 'Otros conceptos', required=False),
            'purchase_ids':fields.one2many('purchase.order', 'work_order_id', 'Compras asociadas', required=False),
            'tipo_parada':fields.selection([
                ('marcha', 'Marcha'),
                ('parada', 'Parada'),
                 ], 'Condicion operación', select=True),
            'state':fields.selection([
                ('draft', 'Borrador'),
                ('open', 'Abierto'),
                ('pending', 'Pendiente de aprobación'),
                ('done', 'Finalizado'),
                ('cancelled', 'Cancelado'),
                 ], 'State', readonly=True),
            'instrucciones': fields.text('Instrucciones'),
            'maintenance_type_id':fields.many2one('maintenance.type', 'tipo de mantenimiento', required=False),
            'survey_id':fields.many2one('survey', 'Encuesta asociada', required=False),
            'descargo':fields.selection([
                ('bloqueo', 'Bloqueo'),
                ('no_descargo', 'No descargo'),
                ('aviso', 'Aviso'),
                 ], 'Descargo', readonly=False),
            'initial_date': fields.date('Fecha inicial'),
            'final_date': fields.date('Fecha final'),

            'responsable_id':fields.many2one('res.users', 'Responsable', required=False),
            'note': fields.text('informe'),
            'padre_id':fields.many2one('work.order', 'orden padre', required=False),
            'hijas_ids':fields.one2many('work.order', 'padre_id', 'Ordenes hijas', required=False),
            'grupo': fields.function(_get_grupo, method=True, type='boolean', string='grupo', store=False),
            'deteccion':fields.text('Detección'),
            'sintoma':fields.text('síntoma'),
            'efecto':fields.text('efecto'),
            'planta':fields.function(_get_planta, method=True, type='char', string='Planta', store={
                                               'work.order': (_get_planta, ['element_ids'], 10),
                                               }),
            'contrata':fields.function(_get_contrata, method=True, type='char', string='Contrata', store=False),
            'elements_list':fields.function(_get_element_list, method=True, type='char', string='string de equipos', store=False),
            'total_other_service':fields.function(_get_total_other_service, method=True, type='float', string='total oros conceptos', store=False),
            'total_servicios_internos':fields.function(_get_total_servicios, method=True, type='float', string='total servicios internos', store=False),
            'total_servicios_externos':fields.function(_get_total_servicios, method=True, type='float', string='total servicios externos', store=False),
                    }
    _defaults = {
        'state':'draft',
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'work.order'),
        'fecha': date.today().strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'work.order', context=c),
        }




    def request_validation(self, cr, uid, ids, context=None):
        self.pool.get('work.order').write(cr, uid, ids, {'state':'pending'}, context)
        return True

    def work_order_cancel(self, cr, uid, ids, context=None):
        self.pool.get('work.order').write(cr, uid, ids, {'state':'cancelled'}, context)
        return True

    def work_order_open(self, cr , uid, ids, context=None):
        self.pool.get('work.order').write(cr, uid, ids, {'state':'open','fecha_inicio':datetime.now()}, context)
        return True

    def work_order_done(self, cr, uid, ids, context=None):
        data_obj = self.pool.get('ir.model.data')
        analytic_line_obj = self.pool.get('account.analytic.line')
        order_obj = self.pool.get('work.order')
        picking_out_obj = self.pool.get('stock.picking.out')
        ordenes = order_obj.browse(cr, uid, ids, context)

        hours_journal_id = data_obj.get_object_reference(cr, uid, 'hr_timesheet', "analytic_journal")[1]
        services_journal_id = data_obj.get_object_reference(cr, uid, 'maintenance', "maintenance_service_journal")[1]
        materials_journal_id = data_obj.get_object_reference(cr, uid, 'maintenance', "maintenance_materials_journal")[1]
        journals = [hours_journal_id, services_journal_id, materials_journal_id]

        for orden in ordenes:


            # calculo de total de costes para horas, servicios y materiales
            coste_total = [0, 0, 0]
            for hora in orden.horas_ids:
                coste_total[0] += hora.total


            coste_total[1]+= orden.total_other_service

            for compra in orden.purchase_ids:
                if compra.state not in ['done', 'approved', 'cancel']:
                    raise osv.except_osv('Compras sin finalizar', 'Compras sin finalizar asociadas a la orden')
                coste_total[1] += compra.amount_total

            for movimiento in orden.stock_moves_ids:
                    if movimiento.state not in ['done', 'cancel']:
                        raise osv.except_osv('movimientos sin finalizar', 'Hay movimientos sin finalizar asociados a la orden')
                    coste_total[2] += movimiento.product_qty * movimiento.product_id.list_price



            # calculo de coste proporcional por equipo
            coste_por_equipo = []
            for coste in coste_total:
                coste_por_equipo.append(coste / len(orden.element_ids))
            aux = 0

            # creacion de apuntes analiticos para cada equipo
            for equipo in orden.element_ids:
                for journal in journals:
                    args_analytic_line = {
                                          'account_id':equipo.analytic_account_id.id,
                                          'journal_id':journal,
                                          'amount':coste_por_equipo[aux],
                                          'product_id':equipo.product_id.id,
                                          'department_id':orden.origin_department_id.id,
                                          'name':equipo.name,
                                          'date':date.today().strftime('%Y-%m-%d'),
                                          }
                    analytic_line_obj.create(cr, uid, args_analytic_line, context)
                    aux += 1

            # creacion del albaran para los movimientos
            args_picking_out = {
                             'work_order_id':orden.id,
                             'origin':orden.name,
                             'date_done':  date.today().strftime('%Y-%m-%d'),
                             'move_lines':[(6, 0, [i.id for i in orden.stock_moves_ids])],
                             'state':'done',
                                     }
            picking_id = picking_out_obj.create(cr, uid, args_picking_out, context)

            order_obj.write(cr, uid, orden.id, {'state':'done'}, context)
        return True


    def send_email(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'maintenance', 'email_template_work_order')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'work.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
work_order()


