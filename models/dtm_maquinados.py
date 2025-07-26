from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime



class Maquinados(models.Model):
    _name = 'dtm.maquinados'
    _description = 'Modulo para llevar el registro de la orden que contendrá los maquinados'
    _rec_name = "orden_trabajo"

    orden_trabajo = fields.Integer(string='OT',readonly=True)
    revision_ot = fields.Integer(string='Versión',readonly=True)
    tipo_orden = fields.Char(string='Tipo',readonly=True)
    disenador = fields.Char(string='Diseñador',readonly=True)

    maquinados_id = fields.One2many('dtm.maquinados.servicios','model_id')

    def action_finalizar(self):
        if not False in self.maquinados_id.mapped('terminado'):
            vals = {
                'orden_trabajo':self.orden_trabajo,
                'revision_ot':self.revision_ot,
                'tipo_orden':self.tipo_orden,
                'disenador':self.disenador,
                'fecha_solicitud':self.create_date
            }
            terminados = self.env['dtm.maquinados.terminados'].search([('orden_trabajo','=',self.orden_trabajo),('revision_ot','=',self.revision_ot),('tipo_orden','=',self.tipo_orden)])
            if terminados:
                raise ValidationError("Este servicio ya se ha realizado")
            else:
                terminados.create(vals)
            terminados = self.env['dtm.maquinados.terminados'].search([('orden_trabajo','=',self.orden_trabajo),('revision_ot','=',self.revision_ot),('tipo_orden','=',self.tipo_orden)])
            for servicio in self.maquinados_id:
                servicio.write({
                                    'model_id': None,
                                    'model2_id': terminados.id,
                                    'terminado': False
                                })
            procesos = self.env['dtm.proceso'].search([('ot_number','=',self.orden_trabajo),('tipe_order','=',self.tipo_orden),('revision_ot','=',self.revision_ot)])
            if procesos:
                procesos.write({
                    'status':'calidad'
                })
            self.unlink()
        else:
            raise ValidationError("Todos los servicios deben estar terminados")


class Servicios(models.Model):
    _name = 'dtm.maquinados.servicios'
    _description = 'Modulo para relacionar los maquinados asociados a una orden'

    model_id = fields.Many2one('dtm.maquinados')
    model2_id = fields.Many2one('dtm.maquinados.terminados')

    nombre = fields.Char(string="Nombre del Servicio", readonly=True)
    tipo_servicio = fields.Char(string="Tipo de Servicio", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", readonly=True)
    material_id = fields.Many2many("dtm.materials.line", readonly=True)
    anexos_id = fields.Many2many("ir.attachment", readonly=True)
    terminado = fields.Boolean()

class Terminado(models.Model):
    _name = "dtm.maquinados.terminados"
    _description = "Modelo para llevar el registro de los maquinados terminados"
    _rec_name = "orden_trabajo"

    orden_trabajo = fields.Integer(string='OT', readonly=True)
    revision_ot = fields.Integer(string='Versión', readonly=True)
    tipo_orden = fields.Char(string='Tipo', readonly=True)
    disenador = fields.Char(string='Diseñador', readonly=True)
    fecha_solicitud = fields.Datetime(string='Fecha de Solicitud', readonly=True)
    duracion = fields.Float(string="Tiempo de Maquinado (Hrs)", compute='_compute_duracion')
    maquinados_id = fields.One2many('dtm.maquinados.servicios', 'model2_id')


    def _compute_duracion(self):
        for result in self:
            result.duracion = round((result.create_date - result.fecha_solicitud).total_seconds() / 3600.0, 2)
