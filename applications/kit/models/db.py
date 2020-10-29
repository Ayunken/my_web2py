# -*- coding: utf-8 -*-
if False:
    from gluon import *
    from db import *
    from custom import *
    from basic_custom import *
    from ..models.custom import *
    from ..models.basic_custom import *
    from ..models._kit import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------
if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig
from basic import *
from gluon.debug import dbg
import datetime
from  plugin_jschosen import jschosen_widget_multiple,jschosen_widget

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),fake_migrate_all=True, lazy_tables=True,
             check_reserved=['common'],db_codec='latin1')
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager
from plugin_lazy_options_widget import lazy_options_widget

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
service = Service()
plugins = PluginManager()

auth.settings.extra_fields[auth.settings.table_user_name] = [
    Field('desactivado','boolean',writable=False,readable=False),
    Field('language_code',length=5,default=T.accepted_language,requires=IS_IN_SET(T.get_possible_languages())),
    ]


# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
auth.define_tables(username=True, signature=False)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')
auth.settings.expiration=3600*24*30
auth.settings.long_expiration=auth.settings.expiration
auth.settings.remember_me_form = True
#
# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)

from plugin_selectplus import SelectOrAddOption, AutocompleteWidgetSelectOrAddOption, SelectTreeWidget
from basic  import Compute_lazy
#funciones comunes para validaciones

#Tablas no migrables, se definen los campos que interesan
SQL_TIME_FORMAT="%Y%m%d %H:%M:%S"
gral=GRAL
current.gral=gral
#IDIOMAS
db.define_table('idiomas',
   Field('id_idioma','id'),
   Field('name',rname='DesIdioma',label=T('Idioma'),length=30,requires=IS_NOT_EMPTY()),
   Field('iso_code',rname='Codigo2',length=2,requires=IS_NOT_EMPTY()),
    format=lambda r: r.name,singular='Idioma',plural='Idiomas',
    migrate=False)
#Unidades de Medida
db.define_table('mod_um',
   Field('name',rname='descri',label=T('U.Medida'),length=30,requires=IS_NOT_EMPTY()),
   Field('cod_SI',rname='abreviatura',label=T('Abreviatura'),length=10,requires=IS_NOT_EMPTY()),
   Field('main_um','integer',label='UM Principal'),
   Field('cod_uni','string',length=4,label='Cod_Uni'),
   Field('factor','float'),
   format=lambda r: r.name if r else "",
               singular='Unidad de medida',plural='Unidades de medida',
               rname='unidades',migrate=False)
db.mod_um.main_um.requires=IS_EMPTY_OR(IS_IN_DB(db,db.mod_um,'%(name)s',orderby=db.mod_um.name))
db.mod_um.main_um.represent=lambda val,registro: '' if val is None else (db.mod_um(val).name or 'Missing')
db.mod_um.factor.show_if = (db.mod_um.main_um !='')
#db.mod_um.main_um.widget=SelectOrAddOption(db.mod_um)
python2=(sys.version<'3')

def bdcodifica(str):
    """Codifica en el codec de la base de datos"""

    if python2:
        return str.decode('utf8').encode(db._db_codec )
    else:
        return str
#Tablas propias

### Tablas jerárquicas #########################################################
from plugin_mptt import MPTT
mptt = MPTT(db)
mptt.settings.table_node_name = 'mod_tipos'
mptt.settings.extra_fields = {
    mptt.settings.table_node_name :
        [Field('name'),
         Field('node_type'),
         Field('abreviatura',length=50,compute=lambda r: r['name'][0:50]),
         Field('created_on', 'datetime', default=request.now)]
}
mptt.define_tables()
db.mod_tipos._plural='Ubicaciones Kit'
db.mod_tipos._singular='Ubicacion Kit'

mptt2 = MPTT(db)
mptt2.settings.table_node_name = 'mod_tipos2'
mptt2.settings.extra_fields = {
    mptt2.settings.table_node_name :
        [Field('name'),
         Field('node_type'),
         Field('abreviatura',length=50,compute=lambda r: r['name'][0:50]),
         Field('created_on', 'datetime', default=request.now)]
}
mptt2.define_tables()
db.mod_tipos2._plural='Tipos de Kit'
db.mod_tipos2._singular='Tipo de Kit'


mptt_atr = MPTT(db)
mptt_atr.settings.table_node_name = 'mod_grp_atr'
mptt_atr.settings.extra_fields = {
    mptt_atr.settings.table_node_name :
        [Field('name'),
         Field('node_type'),
         Field('created_on', 'datetime', default=request.now)]
}
mptt_atr.define_tables()
db.mod_grp_atr._plural='Grupos de atributos'
db.mod_grp_atr._singular='Grupo de atributos'

atr_id=request.args[-1] if len(request.args) > 1 and not 'new' in request.args else None

######################## MAESTRO DE ATRIBUTOS
db.define_table('mod_atr',
                Field('name',length=100,rname='descripcion',requires=IS_NOT_EMPTY(),label='Descripción'),
                Field('clave',length=20,rname='breve',requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mod_atr.clave')],comment='Nombre usado en fórmulas'),
                Field('um',db.mod_um,default=1,label='U.Medida',requires=IS_EMPTY_OR(IS_IN_DB(db,db.mod_um,'%(name)s',orderby=db.mod_um.name))),
                Field('grp_atr',db.mod_grp_atr,label='Grupo',requires=IS_IN_DB(db(db.mod_grp_atr.parent>0),db.mod_grp_atr,'%(name)s',orderby=db.mod_grp_atr.name)),
                Field('tipo','string',length=1,represent=lambda v,r: MOD_ATR_TIPO.getitems()[v]),
                Field('val_def','integer',label='Valor predet.'),
                Field('val_def_formula','string',length=100,label='Fórmula predet.'),
                Field('rango','string',length=50,comment='Formato: "min,max,inc". Ej: desde 2.5 hasta 300, cada 2.5: "2.5,300,2.5"') ,
                Field('abreviatura',length=10,comment='Usada para construir descripcion de módulo. Escribir "%s" para indicar la posición del valor'),
                Field('orden_descripcion','integer',label='Orden',comment="0-999 donde 999 es el primero"),
                Field('visibilidad','string',length=100,label='Visibilidad',comment='Fórmula que debe devolver verdadero o falso, ej: [abc]',default=1),
                Field('comments', 'text'),
                format=lambda r: r.name,singular='Atributo',plural='Atributos',
                rname='proatr_atr',migrate=False)
db.mod_atr.clave.widget=Input_compute_in_form('$("#mod_atr_name").val().split(" ").map(function(v,i,a){return v.toLowerCase().substring(0,3)}).join("_").substring(0,%s)' % db.mod_atr.clave.length)
db.mod_atr.abreviatura.widget=Input_compute_in_form('($("#mod_atr_name").val()) ? $("#mod_atr_name").val().substring(0,3)+"%s" : ""' )
db.mod_atr.grp_atr.represent=lambda v,r: db.mod_grp_atr(v).name if v else ''
db.mod_atr.val_def_formula.requires=IS_EMPTY_OR(IS_FORMULA(db,db.mod_atr.clave,current_atr_id=atr_id))
db.mod_atr.visibilidad.requires=IS_EMPTY_OR(IS_FORMULA(db,db.mod_atr.clave,current_atr_id=atr_id))
db.mod_atr.rango.requires=IS_EMPTY_OR(IS_RANGE(db,db.mod_atr.clave))
db.mod_atr.val_def_formula.represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)
db.mod_atr.rango.represent=lambda v,r: IS_RANGE.formatea(db,v,db.mod_atr.clave)
#db.mod_atr.val_def_formula.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave, form_title='',keyword='mod_atr_val_def_formula',min_length=1,multi=True,add_option=False, orderby='clave')
db.mod_atr.visibilidad.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave, form_title='',keyword='mod_atr_visibilidad',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
#Tablas de valores fijas en memoria
db.mod_atr.tipo.requires=IS_IN_SET(MOD_ATR_TIPO.getitems(),zero=None)
db.mod_atr.rango.show_if=(db.mod_atr.tipo!=MOD_ATR_TIPO.valores)
db.mod_atr.val_def.show_if=(db.mod_atr.tipo==MOD_ATR_TIPO.valores)
db.mod_atr.val_def_formula.show_if=(db.mod_atr.tipo!=MOD_ATR_TIPO.valores)
db.mod_atr.val_def.represent=lambda v,r: db()

########################## MAESTROS DE VALORES DE ATRIBUTOS
db.define_table('mod_val',
                Field('atr',db.mod_atr,rname='atributo',requires=IS_IN_DB(db,db.mod_atr,'%(name)s',orderby=db.mod_atr.name)),
                Field('valor','string',length=50,requires=IS_NOT_EMPTY(),comment='Valor a usar en cálculos en fórmulas'),
                Field('name',label=T('Descripción'),length=100,requires=IS_NOT_EMPTY()),
                Field('abreviatura','string',rname='valorbreve',length=15),
                Field('codigo','string',length=50),
                format=lambda r: r.name , singular='Valor',plural='Valores',
                #format=lambda r: r.name + (db.mod_atr(r.mod_atr).um if r.mod_atr else ''), singular='Valor',plural='Valores',
                rname='proatr_val',migrate=False)
if 'mod_val' in request.args:
    if 'mod_atr_id' in request.vars:
          db.mod_val.name.widget=Input_compute_in_form('$("#mod_val_valor").val()+" %s"' % db.mod_um(db.mod_atr(request.vars.mod_atr_id).um).cod_SI if db.mod_atr(request.vars.mod_atr_id).um else '')

#db.mod_val._before_insert.append( lambda r: record_validator(db.mod_val,r))
#db.mod_val._before_update.append( lambda s,r:record_validator(db.mod_val,r,s.select()[0]))

#campos de atributos que depende de la tabla valores y los amplio ahora en sus definiciones
#db.mod_atr.val_def_disp.compute=lambda r: db.mod_atr.val_def_formula.represent(r['val_def_formula'],r) if r['tipo']==MOD_ATR_TIPO.formula else (db.mod_val(r['val_def']).name if  r['val_def'] else '')
#como la lista de valores la queremos filtrada por el atributo en curso, hay que averiguar el id de atributo
if 'mod_atr' in request.args and not 'new' in request.args:
    request.vars.mod_atr_id=request.args[-1]
    db.mod_atr.val_def.requires=IS_EMPTY_OR(IS_IN_DB(db(db.mod_val.atr==request.vars.mod_atr_id), db.mod_val.id,'%(name)s',orderby=db.mod_val.name))


db.mod_atr.rango.represent = lambda v,r: (', '.join([val.name for val in db(db.mod_val.atr==r.id).select(db.mod_val.name,orderby=db.mod_val.valor)])) \
    if r.tipo==MOD_ATR_TIPO.valores  else  IS_RANGE.formatea(db,v,db.mod_atr.clave)

db.mod_atr.val_def.represent=lambda v,r : (db.mod_val(r.val_def).name if  r.val_def else '') \
        if r.tipo==MOD_ATR_TIPO.valores else db.mod_atr.val_def_formula.represent(r.get('val_def_formula'),r)

#virtual field va bien en version 2.20 no va bien en v2.16, usamos respresent en campos val_def y rango
"""db.mod_atr.rango_disp=Field.Virtual(lambda r: (', '.join([val.name for val in db(db.mod_val.atr==r['mod_atr']['id']).select(db.mod_val.name,orderby=db.mod_val.valor)]))
    if r['mod_atr.tipo']==MOD_ATR_TIPO.valores  else db.mod_atr.rango.represent(r['mod_atr']['rango'],r),label='Rango')

db.mod_atr.val_def_disp=Field.Virtual(lambda r: db.mod_atr.val_def_formula.represent(r['mod_atr'].val_def_formula,r)
    if r['mod_atr'].tipo!=MOD_ATR_TIPO.valores else (db.mod_val(r['mod_atr'].val_def).name if  r['mod_atr'].val_def else ''), label="Valor def.")

db.mod_atr.val_def_disp.length=10
db.mod_atr.rango_disp.length=30
"""
db.mod_atr.val_def_formula.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='fordefval', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_atr.rango.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='forrango', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
mod_atr_id=0
################################## PIEZAS   ##################################################################
#PRODUCTOS,
db.define_table('productos',
   Field('id','id',rname='id_pieza'),
   Field('codigo','string',rname='cod_pie',label='Codigo',length=8,requires=IS_NOT_EMPTY()),
   Field('name','string',rname='descri',label='Descripción',length=80),
   Field('kg_real','float'),
   Field('origen','integer'),
   Field('piezasembalaje','int'),
   Field('idembalaje','integer'),   Field('idembalajeprincipal','integer'),
   Field('cod_uni','integer',represent =lambda val,registro: '' if val is None else db.mod_um(db.mod_um.cod_uni==val).name or 'Missing'),
   format=lambda r: r.name if r else "",singular='Pieza',plural='Piezas',migrate=False
 )

################################## MODULOS  #########################################################################################
db.define_table('mod',
   Field('name',label='Descripción',length=200,writable=False),
   Field('name_fix',label='Descripción fija',length=200),
   Field('tipo', 'list:reference db.mod_tipos', represent=lambda v, j: formatea_multiple(
                    [(db.mod_tipos(i).name) if db.mod_tipos(i) else 'NOEXISTE(%s)' % i for i in v] if v else ''),
                      label='Ubicaciones',
                      requires=IS_IN_DB(db(db.mod_tipos.parent > 0), db.mod_tipos, '%(name)s', multiple=True,
                                        orderby=db.mod_tipos.name)),
   Field('tipo2',db.mod_tipos2,label='Tipo',requires=IS_IN_DB(db(db.mod_tipos2.parent>0),db.mod_tipos2,'%(name)s',orderby=db.mod_tipos2.name)),
   Field('um',db.mod_um,label='U.Medida',default=1,requires=IS_IN_DB(db,db.mod_um,'%(name)s',orderby=db.mod_um.name)),
   format=lambda r: r.name if r else "",singular='Kit', plural='Kits')
db.mod.um.widget=jschosen_widget
db.mod.tipo2.represent=lambda v,r: db.mod_tipos2(v).name if v else ''
db.mod.tipo.widget=jschosen_widget_multiple
db.mod.tipo2.widget=jschosen_widget
#db.mod.tipo.widget=SelectTreeWidget(request,mptt,db.mod_tipos.name, id_field=db.mod_tipos.id,db=db, keyword="modtip")

db.mod.name.widget=Compute_lazy(lambda value,trigger,reg: db.mod_tipos(reg['tipo']).name if not reg['name_fix'] else reg['name_fix']  , triggers=[db.mod.name_fix],user_signature=True,visible=True)

#db.mod.name.widget=Input_compute_in_form('$("#mod_name_fix").val()',set_if_null=False)

def mod_after_update(r,s=None):
    if s:
        for reg in s.select():
            des=monta_descripcion_modulo(db,reg)
            if des!=reg.name:
                db(db.mod.id==reg.id).update_naive(name=bdcodifica(des))
            agrega_refresco(db.mod.name,reg['id'],des)
    return
#db.mod_cmp._before_insert.append( lambda r: record_validator(db.mod_cmp,r))
#db.mod_cmp._before_update.append( lambda s,r: record_validator(db.mod_cmp,r,s.select()[0]))
db.mod._after_update.append( lambda s,r: mod_after_update(r,s))
db.mod._after_insert.append( lambda r,i: mod_after_update(r,db(db.mod.id==i)))
def mod_tipos_after_update(r,s=None):
    if s:
        for reg in s.select(db.mod.ALL,join=db.mod.on(db.mod.tipo.contains(db.mod_tipos.id))):
            des=monta_descripcion_modulo(db,reg)
            if reg.name!=des:
                db(db.mod.id==reg['id']).update_naive(name=bdcodifica(des))
                agrega_refresco(db.mod.name,reg['id'],des)
    return
db.mod_tipos._after_update.append( lambda s,r: mod_tipos_after_update(r,s))

def mod_atr_after_update(r,s):
    if s:
        for reg in s(db.mod_mod_atr.atr==db.mod_atr.id)(db.mod_mod_atr.mod==db.mod.id).select(db.mod.ALL):
            des=monta_descripcion_modulo(db,reg)
            if reg['name']!=des:
                db(db.mod.id==reg['id']).update_naive(name=bdcodifica(des))
                agrega_refresco(db.mod.name,reg['id'],des)
    return
db.mod_atr._after_update.append( lambda s,r: mod_atr_after_update(r,s))


#Modulos Piezas/modulos Vista
"""
SELECT   'P' as tipo, cod_pie as codigo,dbo.finpieza.DESCRI as name from dbo.finpieza
union select  'M' as tipo,'' as codigo, dbo.mod.name from dbo.mod
"""
db.define_table('mod_mod_pie',
                Field('tipo','string',length=1),
                Field('codigo','string',length=15),
                Field('name','string',label='Descripción',length=60),migrate=False)

########################## COMPONENTES DE MODULO #######################################################################################
db.define_table('mod_cmp',
   Field('mod',db.mod,label=T('Kit'),requires=IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name)),
   Field('cmp_tipo','string',length=1,default=MOD_CMP_TIPO.pieza,label='Pza/Mod',requires=IS_IN_SET(MOD_CMP_TIPO().getitems(),zero=None)),
   Field('cmp_pie','integer',label='Pieza comp.',requires=IS_NULL_OR(IS_IN_DB(db,db.productos,'%(name)s',orderby=db.productos.name))),
   Field('cmp_mod','integer',label='Kit comp.', requires=IS_NULL_OR(IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name))),
   Field('formula',default='1',requires=IS_FORMULA(db,db.mod_atr.clave),represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
   singular='Componente',plural='Componentes',
   )
db.mod_cmp.cmp_pie.widget=AutocompleteWidgetSelectOrAddOption(request, db.productos.name,keyword='cmppie', id_field=db.productos.id,min_length=1)
db.mod_cmp.cmp_mod.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='cmpmod',  id_field=db.mod.id, min_length=1,controller='mod',function='view_mod_tabs')
db.mod_cmp.formula.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='modcmp', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_cmp.cmp_tipo.represent=lambda val,row: MOD_CMP_TIPO().getitems()[val]
db.mod_cmp.cmp_pie.show_if=(db.mod_cmp.cmp_tipo==MOD_CMP_TIPO.pieza)
db.mod_cmp.cmp_mod.show_if=(db.mod_cmp.cmp_tipo==MOD_CMP_TIPO.modulo)

def mod_cmp_after_update(r,s):
    if s:
        if 'cmp_tipo' in r:
            if r['cmp_tipo']==MOD_CMP_TIPO.pieza and r['cmp_mod']!=None:
                s.update_naive(cmp_mod=None)
            elif r['cmp_tipo']==MOD_CMP_TIPO.modulo and r['cmp_pie']!= None:
                s.update_naive(cmp_pie=None)
    return
#db.mod_cmp._before_insert.append( lambda r: record_validator(db.mod_cmp,r))
#db.mod_cmp._before_update.append( lambda s,r: record_validator(db.mod_cmp,r,s.select()[0]))
db.mod_cmp._after_update.append( lambda s,r: mod_cmp_after_update(r,s))

#Piezas desarrolladas dsde modulos del modulo mediante una vista de SqlServer
db.define_table('mod_pie',
                Field('mod',db.mod,length=1),
                Field('cmp_pie',db.productos),
                Field('cmp_mod', 'integer'),
                Field('formula'),
                Field('nivel','integer'),
                migrate=False, rname="view_mod_desarrollo_piezas_formula")

#Piezas desarrolladas calculadas desde vista de SqlServer y evaluando las formulas
db.define_table('mod_pie_fin',
                Field('mod',db.mod),
                Field('cmp_pie',db.productos),
                Field('cantidad','float'),
                Field('formula','string',requires = IS_EMPTY_OR(IS_FORMULA(db, db.mod_atr.clave)),
                      represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
                Field('nivel','integer'),
                migrate=True, )
#Modulos desarrollados desde modulos del modulo mediante una vista de SqlServer, usada para ver dónde se utiliza un módulo
db.define_table('mod_mod',
                Field('mod',db.mod),
                Field('cmp_mod',db.mod),
                Field('cantidad',rname='formula'),
                Field('nivel','integer'),
                migrate=False, rname="view_mod_desarrollo_mod_formula")

########################## FILTRO PARA CAMBIO DE PIEZAS EN MODULOS #####################################
db.define_table('mod_rul',
   Field('name','string',length=100,label='Descripción'),
   Field('filtro_descripcion','string',length=200),
   singular='Regla',plural='Reglas para Modificar Kits',
   )
db.define_table('mod_rul_lin',
   Field('mod_rul',db.mod_rul,label=T('Regla')),
   Field('orden','integer'),
   Field('tipo_trg', 'string', length=1, default=MOD_CMP_TIPO.pieza, label='Tipo Origen', requires=IS_IN_SET(MOD_CMP_TIPO().getitems(True),zero=None)),
   Field('cmp_pie_trg','integer',label='Pieza Origen',requires=IS_NULL_OR(IS_IN_DB(db,db.productos,'%(name)s',orderby=db.productos.name))),
   Field('cmp_mod_trg','integer',label='Kit Origen',requires=IS_NULL_OR(IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name))),
   Field('formula_trg','string',label='Fórm.Origen',default=None,requires=IS_NULL_OR(IS_FORMULA(db,db.mod_atr.clave)),represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
   Field('tipo_tar', 'string', length=1, default=MOD_CMP_TIPO.pieza, label='Tipo Destino', requires=IS_IN_SET(MOD_CMP_TIPO().getitems(True), zero=None)),
   Field('cmp_pie_tar','integer',label='Pieza Destino',requires=IS_NULL_OR(IS_IN_DB(db,db.productos,'%(name)s',orderby=db.productos.name))),
   Field('cmp_mod_tar','integer',label='Kit Destino',requires=IS_NULL_OR(IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name))),
   Field('formula_tar','string',label='Fórm.Destino',default='@%s'%ATR_ESPECIAL.PZORIGEN,requires=IS_NULL_OR(IS_FORMULA(db,db.mod_atr.clave)),represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
   singular='Línea de regla',plural='Líneas de Regla',
   )
##112 es el id del atributo variable especial PZORIG, que llevará la cantidad de la pieza original
db.mod_rul_lin.cmp_pie_trg.widget=AutocompleteWidgetSelectOrAddOption(request, db.productos.name,keyword='cmppietrg', id_field=db.productos.id,min_length=1)
db.mod_rul_lin.cmp_pie_tar.widget=AutocompleteWidgetSelectOrAddOption(request, db.productos.name,keyword='cmppietar', id_field=db.productos.id,min_length=1)
db.mod_rul_lin.formula_trg.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='fortrg', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_rul_lin.formula_tar.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='fortar', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_rul_lin.cmp_mod_trg.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='cmpmodtrg',  id_field=db.mod.id, min_length=1)
db.mod_rul_lin.cmp_mod_tar.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='cmpmodtar',  id_field=db.mod.id, min_length=1)
db.mod_rul_lin.tipo_tar.represent=lambda val,row: MOD_CMP_TIPO().getitems()[val]
db.mod_rul_lin.tipo_trg.represent=lambda val,row: MOD_CMP_TIPO().getitems()[val]
db.mod_rul_lin.cmp_pie_trg.show_if=(db.mod_rul_lin.tipo_trg==MOD_CMP_TIPO.pieza)
db.mod_rul_lin.cmp_mod_trg.show_if=(db.mod_rul_lin.tipo_trg==MOD_CMP_TIPO.modulo)
db.mod_rul_lin.cmp_pie_tar.show_if=(db.mod_rul_lin.tipo_tar==MOD_CMP_TIPO.pieza)
db.mod_rul_lin.cmp_mod_tar.show_if=(db.mod_rul_lin.tipo_tar==MOD_CMP_TIPO.modulo)
db.mod_rul_lin.formula_trg.show_if=(db.mod_rul_lin.tipo_trg!=MOD_CMP_TIPO.ninguno)
db.mod_rul_lin.formula_tar.show_if=(db.mod_rul_lin.tipo_tar!=MOD_CMP_TIPO.ninguno)
###################################### ATRIBUTOS DE MODULO / PLANTILLA / CONFIGURACION
#funcion que define una tabla y sus requires y atributos para ser atributos hijos de una tabla
def define_atributos_atr(tablename,padre,campopadre):
    db.define_table(tablename,
    Field(campopadre,db[padre],label=T(db[padre]._singular)),
    Field('atr',db.mod_atr,label=T('Atributo'),requires=IS_IN_DB(db,db.mod_atr,'%(name)s',orderby=db.mod_atr.name,zero='Elija un valor')),
    Field('valores','list:reference db.mod_val',label='Rango valores',represent=lambda v,j: (', '.join([db.mod_val(i).name if db.mod_val(i) else '%s!'% i for i in v])) if v else ''),
    Field('rango','string',label='Rango fórmula',comment=db.mod_atr.rango.comment),
    Field('val_def', 'integer', label='Valor predet.'),
    Field('val_def_formula', 'string',length=100, label='Fórmula predet.'),
    #Field('val_def_disp',label='Valor predet.'),
    #Field('rango_disp','string',label='Rango disp.'),
    Field('tipo','string',length=1),
                    #,compute=lambda r: db.mod_atr(r.atr).tipo if r.atr else None),
    Field('lock','boolean',label='Manual',default=True),
    singular='Atributo de %s' %db[padre]._singular,plural='Atributos de %s' % db[padre]._singular)
    #actualizaciones antes y despues
    tabla=db[tablename]
    tabla.valores.requires=IS_EMPTY_OR(IS_IN_DB(db(db.mod_val.atr>0), db.mod_val.id,'%(name)s',multiple=True,zero='-/-',orderby=db.mod_val.name))
    tabla.rango.show_if=(tabla.tipo!=MOD_ATR_TIPO.valores )
    tabla.rango.requires = IS_EMPTY_OR(IS_RANGE(db, db.mod_atr.clave))
    tabla.rango.represent=lambda v,r:  represent_rango(r)
    tabla.val_def_formula.show_if=(tabla.tipo!=MOD_ATR_TIPO.valores)
    tabla.val_def.show_if=(tabla.tipo==MOD_ATR_TIPO.valores)
    tabla.valores.show_if=(tabla.tipo==MOD_ATR_TIPO.valores)
    tabla.val_def.requires=IS_EMPTY_OR(IS_IN_DB(db(db.mod_val.atr>0), db.mod_val.id,'%(name)s',orderby=db.mod_val.name))
    tabla.val_def.represent = lambda v, r: represent_valdef(r)
    tabla.val_def_formula.requires = IS_EMPTY_OR(IS_FORMULA(db, db.mod_atr.clave))
    def represent_rango(r):
        row=tabla(r['id'])
        if row.tipo==MOD_ATR_TIPO.valores:
            return tabla.valores.represent(row.valores, row)
        else:
            return IS_FORMULA.formatea_ro(db,row.rango,db.mod_atr.clave)
    def represent_valdef(r):
        row = tabla(r['id'])
        if row['tipo']!=MOD_ATR_TIPO.valores:
            return IS_FORMULA.formatea_ro(db,row['val_def_formula'], db.mod_atr.clave)
        else:
            if row['val_def']:
                return db.mod_val(row['val_def']).name
            else:
                return ''


    #tabla.tipo.default=MOD_ATR_TIPO.valores
    select_atr_id='%s_atr' % tabla._tablename
    tabla.atr.widget=SelectOrAddOption( db.mod_atr, select_id=select_atr_id,controller='tablas',function='view_mod_atr_tabs')
    #tabla.atr.widget=jschosen_widget

    mod_atr_id=0 #es variable global (la he establecido al principio para que tambien valga esto para atributo de pieza
    mod_atr_valores=[]
    if tabla._tablename in request.args:
        if 'new' in request.args:
            if 'atr' in request.post_vars:
                mod_atr_id=request.post_vars.atr
        else:
            reg=tabla(request.args[-1])
            if reg:
                 mod_atr_id=reg.atr

######################################## COMPUTE LAZY copia tipo de atributo en el atributo hijo
    r=db.mod_atr[mod_atr_id]
    if r:
        tabla.rango.default = r.rango

    tabla.tipo.widget = Compute_lazy(
        lambda value, trigger, reg: (db.mod_atr(reg['atr']).tipo or '') if reg['atr'] else '',
        triggers=[tabla.atr], user_signature=True, visible=False)


    widget0 = AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave, keyword=tablename,
                                                                       form_title='', min_length=1, multi=True,
                                                                       add_option=False, orderby=db.mod_atr.clave)
    #añadimos el wiget para calculo perezoso, pasandole como argumento el widget el que queremos para el campo y que le añada el js para lo del comupte lazy
    tabla.val_def_formula.widget= Compute_lazy(
        lambda value, trigger, reg: IS_FORMULA.formatea(db,db.mod_atr(reg['atr']).val_def_formula, db.mod_atr.clave) if reg['atr'] else '',
        triggers=[tabla.atr], user_signature=True, visible=False,widget_custom=widget0 )

    tabla.rango.widget = Compute_lazy(
        lambda value, trigger, reg: db.mod_atr.rango.represent(db.mod_atr(reg['atr']).rango,None) if reg['atr'] else '',
        triggers=[tabla.atr], user_signature=True, visible=False, widget_custom=widget0)

    tabla.valores.widget = lazy_options_widget(
                      select_atr_id,
                      lambda v: (db.mod_val.atr == v),
                      mod_atr_id, #VARIABLE TRIGGERM, HA DE COINCIDIR SU NOMBRE CON LA VARIABLE DEL FORMULARIO  mod_mod_mod.atr -> request.vars.atr
                      orderby=db.mod_val.name,
                      user_signature=True,
                      # If you want to process ajax requests at the time of the object construction (not at the form rendered),
                      # specify your target field in the following:
                      field=tabla.valores,multiple=True,
                     lazy_default=lambda v: db.mod_atr[v].val_def if v else None)

    tabla.val_def.widget = lazy_options_widget(
        select_atr_id,
        lambda v: (db.mod_val.atr == v),
        mod_atr_id, orderby=db.mod_val.name,
        user_signature=True,
        field=tabla.val_def, multiple=False,
        lazy_default=lambda v: (db.mod_atr[v].val_def if v else None))

    if request.args:
        if tabla._tablename in request.args: #carga inicial de valores al mostrar registro
            response.js="""
            function fatrvaldef_set(){
             $('#%(tabla)s_val_def option').remove(); \
                  var $options = $('#%(tabla)s_valores option:selected').clone(); \
                  $('#%(tabla)s_val_def').append($options)}
            $('#%(tabla)s_valores').change(function(e){ fatrvaldef_set()}); \
            fatrvaldef_set();
            """% dict(tabla=tabla._tablename)
    #LA ANTERIOR JS NO FUNCIONA CUANDO ES REGISTRO NUEVO O SIN DATOS.
            #CUANDO EL REGISTRO EXISTE, SI FUNCIONA

    #def atr_after_update(r,s):
        #if s:
            #sœ.update_naive(tipo=db.mod_atr(r['atr']).tipo)
    #tabla._before_insert.append( lambda r: record_validator(tabla,r))
    #tabla._before_update.append( lambda s,r: record_validator(tabla,r,s.select()[0]))
    #tabla._after_update.append( lambda s,r: atr_after_update(r,s))
    #tabla._after_delete.append( lambda s: atr_after_update(None,s))

define_atributos_atr ('mod_mod_atr','mod','mod')

def mod_mod_atr_after_update(r,s=None):
    def update(reg):
        des=monta_descripcion_modulo(db,reg['mod'])
        db(db.mod.id==reg['mod']).update_naive(name=des)
        agrega_refresco(db.mod.name,reg['mod'],des)
    if s:
        for reg in s.select():
            update(reg)
    else:
          update(r)
    return

db.mod_mod_atr._after_insert.append( lambda r,id: mod_mod_atr_after_update(r))
#db.mod_mod_atr._after_delete.append( lambda s: mod_mod_atr_after_update(s)) ESTO ESTA ANULADO PORQUE NO SÉ COMO HACERLO, REVISARLO CUANDO SEPA QUE HACIA!!!!!!!!!!!!
db.mod_mod_atr._after_update.append( lambda s,r: mod_mod_atr_after_update(r,s))

###################################################### ATRIBUTOS DE PIEZAS
#ATRUTOS DE PIEZAS
db.define_table('mod_pie_atr',
    Field('pieza',db.productos),
    Field('atr',db.mod_atr,label=T('Atributo'),rname='atributo',requires=IS_IN_DB(db,db.mod_atr,'%(name)s',orderby=db.mod_atr.name,zero='Elija un valor')),
    Field('val',db.mod_val,rname='valor',label='valor'),
    Field('valor_especifico','string',represent=lambda v,j: v if v else ''),
    Field('valorfinal', 'string', label='Valor final',writable=False),
    singular='Atributo de pieza',plural='Atributos de pieza',rname='Vista_ProAtr_AtributosPieza',migrate=False)
select_atr_id='mod_pie_atr_atr'
db.mod_pie_atr.atr.widget=SelectOrAddOption( db.mod_atr, select_id=select_atr_id,controller='tablas',function='view_mod_atr_tabs')
db.mod_pie_atr.val.widget = lazy_options_widget(
                      select_atr_id,
                      lambda v: (db.mod_val.atr == v),
                      mod_atr_id, #VARIABLE TRIGGERM, HA DE COINCIDIR SU NOMBRE CON LA VARIABLE DEL FORMULARIO  mod_mod_mod.atr -> request.vars.atr
                      orderby=db.mod_val.name,
                      user_signature=True,
                      # If you want to process ajax requests at the time of the object construction (not at the form rendered),
                      # specify your target field in the following:
                      field=db.mod_pie_atr.val,multiple=False,
                     lazy_default=lambda v: (db.mod_atr[v].val_def if v else None)
                      )

def prueba(r):
    if r.adicional:
        return r.cfg_base
    else:
        try: #como el oprow r no lleva el id nunca, pues ha que hacer este giro
            return db(db.mod_cfg.name==r.name).select(db.mod_cfg.id).first().id
        except:
            return
####################### CONFIGURACIONES
mptt_cfg=MPTT(db)
mptt_cfg.settings.table_node_name = 'mod_cfg'
mptt_cfg.settings.extra_fields = {
    mptt_cfg.settings.table_node_name :
        [Field('name'),
         Field('node_type'),
         Field('created_on', 'datetime', default=request.now),
         Field('comments','text',label='Observaciones'),
         Field('breve', 'string', label='Breve')]
}
mptt_cfg.define_tables()
db.mod_cfg._singular='Configuración'
db.mod_cfg._plural='Configuraciones'
db.mod_cfg.format=lambda r: r.name

"""db.define_table('mod_cfg',
   Field('name',label='Descripción',length=100,requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'mod_cfg.name')]),
   Field('cfg_base','reference mod_cfg',label='Configuración Origen'),
   Field('adicional','boolean',label='Configuración adicional',comment='Al crearla, se copiarán sólo los atributos desde la configuración base. Si no es adicional se copian también las ubicaciones'),
   Field('comments','text',label='Observaciones'),
   Field('orden','integer',compute=lambda r:  prueba(r),writable=False,readable=False),
 format=lambda r: r.name ,singular='Configuración', plural='Configuraciones')
db.mod_cfg.cfg_base.requires=IS_EMPTY_OR(IS_IN_DB(db,db.mod_cfg,'%(name)s',orderby=db.mod_cfg.name))
db.mod_cfg.cfg_base.represent=lambda v,r: db.mod_cfg(v).name if v else ''
db.mod_cfg.adicional.show_if = (db.mod_cfg.cfg_base != '')
"""
########################## COMPONENTES DE CONFIGURACION
db.define_table('mod_cfg_mod',
   Field('cfg',db.mod_cfg,label=T('Configuración'),requires=IS_IN_DB(db,db.mod_cfg,'%(name)s',orderby=db.mod_cfg.name,zero=None)),
   Field('mod',db.mod,label='Kit', requires=IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name)),
   Field('formula',default='1',label=T('Fórmula'),requires=IS_FORMULA(db,db.mod_atr.clave),represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
   Field('mod_tipo', db.mod_tipos, label='Tipo', requires=IS_IN_DB(db(db.mod_tipos.parent > 0), db.mod_tipos, '%(name)s',orderby=db.mod_tipos.name),
                represent = lambda v, r: db.mod_tipos(v).name if v else ''),
singular='Componente',plural='Componentes'
   )

########################## TIPOS DE KITS COMPONENTES DE LA CONFIGURACION
db.define_table('mod_cfg_tip',
   Field('cfg',db.mod_cfg,label=T('Plantilla'),requires=IS_IN_DB(db,db.mod_cfg,'%(name)s',orderby=db.mod_cfg.name)),
   Field('mod_tipo',db.mod_tipos,label='Tipo de Kit', requires=IS_IN_DB(db,db.mod_tipos,'%(name)s',orderby=db.mod_tipos.name)),
   Field('min_mods','integer',label="Mínimo de Kits necesarios"),
   Field('formula',default='1',label=T('Fórmula'),requires=IS_FORMULA(db,db.mod_atr.clave),represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)),
   Field('tag','integer',readable=False,writable=False),
   singular='Tipo de Kit de Configuración',migrate=True,plural='Tipos de Kit de Configuración')

db.mod_cfg_tip.mod_tipo.widget=SelectTreeWidget(request,mptt,db.mod_tipos.name, id_field=db.mod_tipos.id,db=db, keyword="modcfgtip")
db.mod_cfg_tip.formula.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='modcfg', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_cfg_mod.formula.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod_atr.clave,keyword='modcfgmod', form_title='',min_length=1,multi=True,add_option=False, orderby=db.mod_atr.clave)
db.mod_cfg_mod.mod_tipo.represent=db.mod_cfg_tip.mod_tipo.represent=lambda v,r: db.mod_tipos(v).name if v else ''
####################### ATRIBUTOS  DE TIPOS DE KIT DE CONFIGURACION
define_atributos_atr ('mod_cfg_tip_atr','mod_cfg_tip','cfg_tip')
db.mod_cfg_tip_atr.lock.label='Heredable'
db.mod_cfg_tip_atr.lock.default=True

################  CONSULTA DE TIPOS de cfg COMBINADA
db.define_table('mod_cfg_tip_combi',
   Field('cfg',db.mod_cfg),
   Field('cfg_tip',db.mod_cfg_tip),
   Field('mod_tipo', db.mod_tipos),
    Field('formula','string'),
    Field('cfg_origen','integer'),
                migrate=False,rname='Vista_Mod_cfgtip_tree_combi')

################  CONSULTA DE ATRIBUTOS DE TIPOS COMBINADA
db.define_table('mod_cfg_tip_atr_combi',
   Field('cfg',db.mod_cfg),
   Field('cfg_tip',db.mod_cfg_tip),
   Field('cfg_tip_atr','id'),
   Field('mod_tipo',db.mod_tipos),
   Field('atr',db.mod_atr),
    Field('valores','list:reference db.mod_val'),
    Field('val_def',db.mod_val),
    Field('val_def_formula','string'),
    Field('rango','string'),
    Field('tipo','string'),
    Field('cfg_tip_ori',db.mod_cfg_tip),
    Field('mod_tipo_ori',db.mod_tipos),
  migrate=False,rname='Vista_Mod_cfgtip_atr_tree_combi')

################  CONSULTA DE ATRIBUTOS de kit vs atributos de config ###
db.define_table('mod_mod_atr_cfg_tip_atr',
   Field('cfg','integer'),
   Field('mod','integer'),
Field('cfg_tip','integer'),
Field('mod_tipo','integer'),
Field('formula','string'),
Field('atr','integer'),Field('tipo','string'),
Field('mod_valores','list:reference db.mod_val'),
Field('tip_valores','list:reference db.mod_val'),

  migrate=False,rname='[Vista_Mod_modatr_cfgtipatr]')
"""
def mod_cfg_after_insert(r,id):
    if r['cfg_base']:
        if r['adicional']:
            rows = db((db.mod_cfg_tip.mod_tipo==IDRAIZ_MOD_TIPO)&(db.mod_cfg_tip.cfg == r['cfg_base'])).select()
        else:
            rows=db(db.mod_cfg_tip.cfg==r['cfg_base']).select()
        for r in rows:
            cfgtip=r.id
            del r.id
            r.cfg=id
            idtip=db.mod_cfg_tip.insert(**r)
            atrs=db(db.mod_cfg_tip_atr.cfg_tip == cfgtip).select()
            for atr in atrs:
                del atr.id
                atr.cfg_tip=idtip
                db.mod_cfg_tip_atr.insert(**atr)

db.mod_cfg._after_insert.append( lambda r,id: mod_cfg_after_insert(r,id)
"""

####################### PRESUPUESTO
db.define_table('mod_pre',
                Field('name','string',rname='descri',length=100),
                Field('fecha','datetime',requires=IS_DATE(),represent = lambda value, row: value.strftime('%d/%m/%Y') if value else ''),
                Field('numero','integer',writable=False),
                Field('cfg',db.mod_cfg,label="Configuración base",requires=IS_IN_DB(db((db.mod_cfg.level==2)),db.mod_cfg,'%(name)s',zero=None,error_message='la configuración debe ser de último nivel')),
                Field('comments', 'text', rname='descri_larga',label='Observaciones'),
                migrate=False,singular='Presupuesto',plural='Presupuestos')
db.mod_pre.cfg.widget=SelectTreeWidget(request,mptt_cfg,db. mod_cfg.name, id_field=db.mod_cfg.id,db=db, keyword="precfg")
db.mod_pre.cfg.represent=lambda v,r: db.mod_cfg(v).get('name') if v else ''
####################### PIEZAS PRESUPUESTO
db.define_table('pre_pie',
                Field('pre',db.mod_pre,rname='cod_pre'),
                Field('pieza',db.productos,rname='id_pieza'),
                Field('cantidad','float',rname='uni_pie'),
                migrate=False,singular='Pieza Presupuesto',plural='Piezas Presupuesto',rname='Piezas_Presupuesto')


####################### subnaves PRESUPUESTO ############ Tabla de los grupos/bloques de naves-modulos con las mismas propiedades
db.define_table('mod_pre_subnaves',
                Field('pre', 'integer'),
                Field('tund', 'integer'),
                Field('tunh','integer'),
                Field('modd','integer'),
                Field('modh','integer'),
                Field('cfg',db.mod_cfg),
                )

####################### MÓDULOS PRESUPUESTO
db.define_table('mod_pre_mod',
                Field('pre',db.mod_pre,writable=False),
                Field('subnave',db.mod_pre_subnaves),
                Field('mod',db.mod,requires=IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name, zero=None)),
                Field('mod_tipo', db.mod_tipos, requires=IS_IN_DB(db, db.mod_tipos, '%(name)s', orderby=db.mod_tipos.name, zero=None)),
                Field('cantidad','float'),
                singular='Kit Presupuesto',plural='Kits Presupuesto')
db.mod_pre_mod.mod_tipo.represent=lambda v,r: db.mod_tipos(v).get('name') if v else ''
db.mod_pre_mod.mod.widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='premod',  id_field=db.mod.id, min_length=1,controller='mod',function='view_mod_tabs')
db.mod_pre_mod.subnave.represent=lambda v,r: db.mod_pre_subnaves(v).get('cfg').breve if v else ''

######################## MODULOS Y SUS PIEZAS DE PRESUPUESTO ###################### DESGLOSE DE CALCULO DE PIEZAS POR MODULO
db.define_table('mod_pre_mod_pie',
                Field('pre', db.mod_pre),
                Field('pre_mod', 'integer'),
                Field('pie', db.productos),
                Field('formula', 'string'),
                Field('cantidad', 'float'),
                migrate=False, singular='Kit-Pieza Presupuesto', plural='Kit-PIezas Presupuesto')

db.mod_pre_mod_pie.formula.represent=lambda v,r: IS_FORMULA.formatea_ro(db,v,db.mod_atr.clave)

####################### atributos PRESUPUESTO
db.define_table('mod_pre_atr',
        Field('pre',db.mod_pre,writable=False),
        Field('subnave',db.mod_pre_subnaves,default=0,comment='Conjunto de atributos que se asignarán a un subbloque de naves'),
        Field('mod_tipo',db.mod_tipos,represent=lambda v,r: db.mod_tipos(v).name if v else '' ),
        Field('atr',  db.mod_atr,label='Atributo'),
        Field('valor','string',length=200),
        Field('valores','list:reference db.mod_val'),
        Field('rango','string'),
        Field('tipo','string'),
        Field('opcional','boolean'),
        Field('tag','boolean'),
                singular='Atributo Presupuesto', plural='Atributos Presupuesto')

db.mod_pre_atr.valor_disp = Field.Virtual(lambda r: db.mod_val(r.mod_pre_atr.valor).name if db.mod_atr(r.mod_pre_atr.atr).tipo==MOD_ATR_TIPO.valores else \
                                                '%s %s' % (r.mod_pre_atr.valor,db.mod_atr(r.mod_pre_atr.atr).um.cod_SI),
                                          label='Valor')
####################### naves PRESUPUESTO
db.define_table('mod_pre_nav',
                Field('pre', 'integer', writable=False),
                Field('posx','integer'),
                Field('posy','float'),
                Field('cfg',db.mod_cfg,label="Configuración base",requires=IS_IN_DB(db,db.mod_cfg,'%(name)s',orderby=db.mod_cfg.name, zero=None)),
                Field('anchonave', db.mod_val, requires=IS_IN_DB(db(db.mod_val.atr == ATRS.nave_ancho), db.mod_val, '%(name)s',
                                        orderby=db.mod_val.name,zero=None)),
                Field('unidades','integer',default=1,requires=IS_INT_IN_RANGE(1,100)),
                Field('longitud','float'),
                singular='Nave Presupuesto', plural='Naves Presupuesto')
db.mod_pre_nav.cfg.represent=lambda v,r: db.mod_cfg(v).name if v else ''
#db.mod_pre_nav.anchonave.widget=Compute_lazy(lambda value,trigger,reg: get_atr_cfg(reg['cfg'],ATRS.nave_ancho),  triggers=[db.mod_pre_nav.cfg],user_signature=True,visible=True)


""" Ejemplos de hacer actalizaciones desdpues de insertar o actualizar
#el parametro s es una set de los registros a actualizar
@el parametro f son los campos
def set_id_after_insert(fields,id):
    fields.update(fullpath=asigna_ruta_mod_tipos(fields,id))

def set_id_after_update(s,f):
    row = s.select().first()
    s.update_naive(fullpath=asigna_ruta_mod_tipos(row,row.id))
db.mod_tipos._after_insert.append(lambda f,id: set_id_after_insert(f,id))
db.mod_tipos._after_update.append(lambda s,f: set_id_after_update(s,f))
"""

# En aquellas tablas de mssql que no tengan UTF8 hay que hacer esto para que codifique en el codec de la bd
def MSACCESS_adapt(s,f):
     for k,v in f.items():
        if type(v)==str:
            f[k] =bdcodifica(v)
            pass
        elif type(v)==datetime.datetime:
              f[k]=v.strftime('%Y-%m-%dT%H:%M:%S')
if python2:
    for i in [db.mod_tipos,db.mod,db.mod_atr,db.mod_cfg,db.mod_val,db.productos, db.mod_pre,db.mod_pre_atr]:
        i._before_update.append(MSACCESS_adapt)
        i._before_insert.append(lambda r: MSACCESS_adapt(None,r))

if auth.user:
    gral.currency_simbol='€'
    T.force(auth.user.language_code or T.accepted_language or 'es')
else:
    T.force(T.accepted_language or 'es')
