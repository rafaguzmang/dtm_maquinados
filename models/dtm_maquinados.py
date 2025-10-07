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

    maquinados_id = fields.One2many('dtm.maquinados.temporales','model_id')

    finalizado = fields.Boolean(compute="_compute_finalizado")
    status = fields.Float(compute="_compute_status")

    def _compute_status(self):
        for record in self:
            record.status = 0
            if record.maquinados_id:
                porcentaje = sum(record.maquinados_id.mapped('status'))
                servicios = len(record.maquinados_id.ids)
                record.status = porcentaje/servicios

    def _compute_finalizado(self):
        for record in self:
            record.finalizado = False
            if False not in record.maquinados_id.mapped('terminado'):
                record.finalizado = True


    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Maquinados,self).get_view(view_id, view_type,**options)
        get_this = self.env['dtm.maquinados'].search([])
        for record in get_this:
           if not record.maquinados_id:
               record.unlink()
        return res

    def action_finalizar(self):
        if not False in self.maquinados_id.mapped('terminado'):
            vals = {
                'orden_trabajo':self.orden_trabajo,
                'revision_ot':self.revision_ot,
                'tipo_orden':self.tipo_orden,
                'disenador':self.disenador,
                'fecha_solicitud':self.create_date,
            }
            # Se busca si ya está terminado
            terminados = self.env['dtm.maquinados.terminados'].search([('orden_trabajo','=',self.orden_trabajo),('revision_ot','=',self.revision_ot),('tipo_orden','=',self.tipo_orden)])
            if terminados:
                terminados.write(vals)
            else:
                terminados = self.env['dtm.maquinados.terminados'].create(vals)
            for servicio in self.maquinados_id:
                vals = {
                    'model2_id':terminados.id,
                    'nombre':servicio.nombre,
                    'tipo_servicio':servicio.tipo_servicio,
                    'cantidad':servicio.cantidad,
                    'fecha_solicitud':servicio.fecha_solicitud,
                    'terminado':True,
                    'anexos_id':servicio.anexos_id,
                    'tiempo_total':servicio.tiempo_total
                }
                get_finalizados = self.env['dtm.maquinados.servicios'].search([
                    ('model2_id','=',terminados.id),
                    ('nombre','=',servicio.nombre)],limit=1)
                if get_finalizados:
                    get_finalizados.write(vals)
                else:
                    get_finalizados = self.env['dtm.maquinados.servicios'].create(vals)
                for tiempo in servicio.tiempos_id:
                    tiempo.write({'model_id':None,'model_id2':get_finalizados.id,})
                # servicio.unlink()
            procesos = self.env['dtm.proceso'].search([('ot_number','=',self.orden_trabajo),('tipe_order','=',self.tipo_orden),('revision_ot','=',self.revision_ot)])
            if procesos:
                procesos.write({
                    'status':'calidad'
                })
            # self.unlink()
            return self.env.ref('dtm_maquinados.dtm_maquinados_act_window').read()[0]

class Servicios(models.Model):
    _name = 'dtm.maquinados.servicios'
    _description = 'Modulo para relacionar los maquinados asociados a una orden'

    model2_id = fields.Many2one('dtm.maquinados.terminados')

    nombre = fields.Char(string="Nombre del Servicio", readonly=True)
    tipo_servicio = fields.Char(string="Tipo de Servicio", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", readonly=True)
    anexos_id = fields.Many2many("ir.attachment", readonly=True)
    terminado = fields.Boolean()
    tiempo_total = fields.Float(string="Tiempo", readonly=True)
    tiempos_id = fields.One2many('dtm.maquinados.tiempos','model_id2')

class Temporales(models.Model):
    _name = 'dtm.maquinados.temporales'
    _description = 'Modulo para relacionar los maquinados asociados a una orden'

    model_id = fields.Many2one('dtm.maquinados')
    nombre = fields.Char(string="Nombre del Servicio", readonly=True)
    tipo_servicio = fields.Char(string="Tipo de Servicio", readonly=True)
    cantidad = fields.Integer(string="Cantidad", readonly=True)
    fecha_solicitud = fields.Date(string="Fecha de Solicitud", readonly=True)
    anexos_id = fields.Many2many("ir.attachment", readonly=True)
    terminado = fields.Boolean()
    start = fields.Boolean()
    contador = fields.Integer()
    status = fields.Float()

    tiempos_id = fields.One2many('dtm.maquinados.tiempos','model_id')
    timer = fields.Datetime()
    tiempo_total = fields.Float(string="Tiempo", readonly=True)

    def action_inicio(self):
        self.start = True
        self.timer = datetime.today()

    def action_stop(self):
        self.start = False
        tiempo = self.tiempos_id.create({
                    'model_id': self.id,
                    'contador': self.contador,
                    'tiempo': round((datetime.today() - self.timer).total_seconds() / 60.0, 4)
                })
        self.tiempo_total = sum(self.tiempos_id.mapped('tiempo'))

    def action_mas(self):
        self.contador += 1
        self.status = (self.contador * 100)/self.cantidad
        if self.contador >= self.cantidad:
            self.terminado = True
            self.action_stop()

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

class Tiempos(models.Model):
    _name = "dtm.maquinados.tiempos"
    _description = "Modelo para llevar el tiempo del trabajo de las máquinas laser"
    _order = "id desc"
    model_id = fields.Many2one('dtm.maquinados.temporales')
    model_id2 = fields.Many2one('dtm.maquinados.servicios')

    contador = fields.Integer(string='Número de láminas', readonly=True)
    tiempo = fields.Float(string='Duración', readonly=True)
