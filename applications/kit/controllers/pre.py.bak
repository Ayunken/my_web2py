# -*- coding: utf-8 -*-
import gluon.contenttype
from plugin_jstree import JsTree
import datetime
from plugin_selectplus import multiTab_widget, SelectTreeWidget
from basic import *
from plugin_lazy_options_widget import lazy_options_widget
if False:
    from ..models.custom import *
    from ..models.basic_custom import *
    from ..models._kit import *
    from ..models.db import *
    from ..models.invernadero import *

@auth.requires_login()
def index(): return dict(message="hello from pre.py")

@auth.requires_login()
def grid_pre_pie():
    filtra_lista_request_vars(request.vars, 'pre_id')
    query=db(db.pre_pie.pre==request.vars.pre_id)
    left=[db.productos.on(db.pre_pie.pieza==db.productos.id)]
    fields=[db.productos.codigo,db.productos.name,db.pre_pie.cantidad]
    grid=SQLFORM.grid(query,links=[],fields=fields,left=left)
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    if not request.args:
        links = [lambda row: A('', _title='Kits Origen',
                           _onclick='openform_precmpmod(%(pre_pie.id)s,"%(productos.name)s - Kits origen");' % row,
                           _class='btn btn-default btn-secondary glyphicon glyphicon-list')
        ]
    else:
        db.pre_pie.pieza.writable=db.pre_pie.pre.writable=db.pre_pie.pre.readable=False
        links=None
    grid=SQLFORM_plus(query,links=links,fields=fields,left=left,field_id=db.pre_pie.id,create=False,title='Piezas',**defaults)()
    grid_addbutton_self(grid, "Calcular Piezas",
                        URL('grid_pre_pie_calc', vars=dict(pre_id=request.vars.pre_id), user_signature=True),
                        confirm=True)
    grid['grid'].components.extend([windows_popup_load('precmpmod', 'grid_pre_cmp_mod', 'pre_pie_id', c='pre')])

    return grid

@auth.requires_login()
def grid_pre_cmp_mod():
    filtra_lista_request_vars(request.vars, 'pre_pie_id')
    id=request.vars.pre_pie_id
    query=db((db.pre_pie.id==id)&(db.mod_pre_mod_pie.pre==db.pre_pie.pre)&(db.pre_pie.pieza==db.mod_pre_mod_pie.pie) & (db.mod_pre_mod_pie.pre_mod==db.mod_pre_mod.id) )
    response.view='grid.%s' % request.extension
    defaults=gral.grid_defaults
    left = [db.mod.on(((db.mod.id == db.mod_pre_mod.mod)))]
    fields = [db.mod_pre_mod.mod_tipo,db.mod_pre_mod.cantidad,db.mod.name,db.mod_pre_mod_pie.formula,db.mod_pre_mod_pie.cantidad]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False,left=left, field_id=db.mod_pre_mod_pie.id, title='Piezas desarrolladas')
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None)
    return dict(**gridp)

@auth.requires_login()
def grid_pre_mod():
    filtra_lista_request_vars(request.vars, 'pre_id')
    query=db(db.mod_pre_mod.pre==request.vars.pre_id)
    left=[db.mod.on(db.mod_pre_mod.mod==db.mod.id)]
    db.mod_pre_mod.pre.default=request.vars.pre_id
    fields=[db.mod_pre_mod.subnave,db.mod.id,db.mod.name,db.mod_pre_mod.mod_tipo,db.mod_pre_mod.cantidad]
    db.mod.id.listable=False
    grid=SQLFORM.grid(query,links=[],fields=fields,left=left)
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    links = [lambda row: A('', _title='Componentes del kit',
                           _onclick='openform_modcmp(%(mod.id)s,"%(mod.name)s - componentes");' % row,
                           _class='btn btn-default btn-secondary glyphicon glyphicon-list'),
             lambda row: A('', _title='Piezas generadas',
                           _onclick='openform_premodcmp(%(mod_pre_mod.id)s,"%(mod.name)s - Piezas generadas");' % row,
                           _class='btn btn-default btn-secondary glyphicon glyphicon-list')
             ]

    grid=SQLFORM_plus(query,links=links,fields=fields,left=left,field_id=db.mod_pre_mod.id,title=db.mod_pre_mod._plural,**defaults)()
    url=URL('grid_pre_mod_calc', vars=dict(pre_id=request.vars.pre_id), user_signature=True)
    grid_addbutton_self(grid, "Calcular Kits", url,      confirm=True)
    grid['grid'].components.extend([windows_popup_load('modcmp', 'grid_mod_cmp0', 'mod_id',c='mod')])
    grid['grid'].components.extend([windows_popup_load('premodcmp', 'grid_pre_mod_cmp', 'pre_mod_id', c='pre')])
    return grid

@auth.requires_login()
def grid_pre_mod_cmp():
    filtra_lista_request_vars(request.vars, 'pre_mod_id')
    id=request.vars.pre_mod_id
    query=db((db.mod_pre_mod_pie.pre_mod==id))
    response.view='grid.%s' % request.extension
    defaults=gral.grid_defaults
    left = [db.mod_mod_pie.on((db.mod_mod_pie.tipo == 'P') & ((db.mod_mod_pie.id == db.mod_pre_mod_pie.pie)))]
    fields = [db.mod_mod_pie.codigo, db.mod_mod_pie.name, db.mod_pre_mod_pie.formula,db.mod_pre_mod_pie.cantidad]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False,left=left, field_id=db.mod_pre_mod_pie.id, title='Piezas desarrolladas')
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None)
    return dict(**gridp)


@auth.requires_login()
def view_pre_tabs0(form,botones):
    reg=db.mod_pre(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], \
         [T('Atributos'), dict(f='grid_pre_atr.load', vars=dict(pre_id=reg.id),user_signature=True)], \
         [T('Naves'), dict(f='grid_pre_naves.load', vars=dict(pre_id=reg.id), user_signature=True)], \
         [T('Matriz'),dict(f='grid_inver.load', vars=dict(pre_id=reg.id),user_signature=True)],\
         [T('Kits'),dict(f='grid_pre_mod.load', vars=dict(pre_id=reg.id),user_signature=True)],\
         [T('Piezas'),dict(f='grid_pre_pie.load',vars=dict(pre_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_pre._singular,tablename='mod_pre')


@auth.requires_login()
def grid_pre():
    tabla=db.mod_pre
    query = tabla
    create=True
    left=[]
    last=db(tabla.numero>0).select(tabla.numero).first()
    if not last:
        last=0
    else:
        last=last.numero
    tabla.numero.default=last+1
    tabla.fecha.default=request.now.date()
    fields=[tabla.numero,tabla.name,tabla.cfg,tabla.comments,tabla.fecha]
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    response.view = 'grid.%s' % request.extension
    grid = SQLFORM_plus(query, links=[], field_id=db.mod_pre.id, create=create, left=left, fields=fields,
                        title=tabla._plural, **defaults)
    if len(request.args) > 1 and not 'new' in request.args:
        return view_pre_tabs0(grid.grid, botones_back(request, f=request.function))
    else:
        return grid()


@auth.requires_login()
def grid_pre_naves():
    pre=filtra_lista_request_vars(request.vars, 'pre_id')
    tabla=db.mod_pre_nav
    query = db(tabla.pre == pre)
    if request.args:
        if pre:
            tabla.pre.default = pre
            tabla.cfg.default = db.mod_pre(pre).cfg
            cfl=db.mod_cfg(tabla.cfg.default).parent
            tabla.cfg.requires = IS_IN_DB(db(db.mod_cfg.parent==cfl), db.mod_cfg, '%(name)s', orderby=db.mod_cfg.name, zero=None)
            tabla.longitud.requires = IS_IN_SET(Formula_Pre(db,pre).get_range_atr(ATRS.nave_long), zero=None)
            tabla.posy.requires = IS_IN_SET(Formula_Pre(db,pre).get_range_atr(ATRS.nave_posy),zero=None)
            DALX.setdefault_contador(tabla.posx,db(tabla.pre==pre))

    mod_cfg_id =  tabla.cfg.default  # es variable global (la he establecido al principio para que tambien valga esto para atributo de pieza
    if 'mod_pre_nav' in request.args:  # chapucilla de sacara el tipo de ubicacion para que el SELECT este populado a la ida para mostrar el registro y a la vuelta el requires IS_IN_DB  para el update
        if 'cfg' in request.post_vars:
            mod_cfg_id = request.post_vars.cfg
        elif 'mod_cfg_id' in request.vars:
            mod_cfg_id = request.vars.mod_cfg_id
        elif 'edit' in request.args:
            reg = db.mod_pre_nav(request.args[-1])
            if reg:
                mod_cfg_id = reg.cfg
    ####
    if request.args:
        db.mod_pre_nav.anchonave.widget = lazy_options_widget(
            "mod_pre_nav_cfg",
            # VARIABLE TRIGGERM, HA DE COINCIDIR SU NOMBRE CON LA VARIABLE DEL FORMULARIO  mod_mod_mod.atr -> request.vars.atr
            lambda v: (db.mod_cfg_tip.cfg == v) & (db.mod_cfg_tip.mod_tipo == IDRAIZ_MOD_TIPO) & (db.mod_cfg_tip_atr.cfg_tip == db.mod_cfg_tip.id) & (db.mod_cfg_tip_atr.atr == ATRS.nave_ancho) & (db.mod_cfg_tip_atr.atr==db.mod_val.atr) &   (db.mod_cfg_tip_atr.valores.contains(db.mod_val.id)) ,
            mod_cfg_id,
            orderby=db.mod_val.name,
            user_signature=True,
            # If you want to process ajax requests at the time of the object construction (not at the form rendered),
            # specify your target field in the following:
            field=db.mod_pre_nav.anchonave, multiple=False,
            lazy_default=None)

    fields =[tabla[i] for i in ('posx','posy','cfg','anchonave','unidades','longitud')]
    response.view = 'grid.%s' % request.extension
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    grid = SQLFORM_plus(query, orderby=[tabla.posx], links=[], fields=fields,field_id=tabla.id, title=tabla._plural, **defaults)
    return grid()
    #MEJORA: FALTA INFERIR EN NUEVAS ALTAS ANCHO Y OFFSET Y DE LA ULTIMA.default

@auth.requires_login()
def grid_pre_atr_modtip_grp(): #grid_pre_atr agrupando por mod_tipo
    filtra_lista_request_vars(request.vars,'pre_id')
    query=((db.mod_pre_atr.pre==request.vars.pre_id)&(db.mod_pre_atr.subnave==0))
    if len(request.args) >0 and '_formname' not in  request.vars: #compruebo si viene _formname porque cunado viene del botón no hay formname, cuando viene de submit por cambio de checks sí,
        #ya que no hay forma de desahacerse de los args pues los propaga en el el redirect cuando viene del callback del botón,
        if request.args(-1):
            recolectar_atributos_presupuesto(db, request.args(-1))
            session.flash = 'Variables calculadas!!!'
            url = URL(request.funcion, args=[], vars=dict(pre_id=request.args(-1)))
            redirect(url)
    else:
        inicial=(db(query).count() == 0)
        recolectar_atributos_presupuesto(db, request.vars.pre_id,inicial=inicial)
    form = FORM(SPAN(INPUT(_name="opcionales", _id='pre_opcionales',_type='checkbox', value=True if session.pre_opcionales else False,
                           _onchange='$("form[name=frmsel]").submit();'), LABEL('Atrib. de diseño',_for='pre_opcionales'),_class='col-sm-2'),
                SPAN(INPUT(_name="detalle", _id='pre_detalle',_type='checkbox', value=True if session.pre_detalle else False,
                           _onchange='$("form[name=frmsel]").submit();'), LABEL('Ubicaciones',_for='pre_detalle'),_class='col-sm-2'),
                _name="frmsel")
    if form.accepts(request.vars,formname='frmsel',keepvalues=True):
        session.pre_opcionales = form.vars.opcionales
        session.pre_detalle = form.vars.detalle

    if not session.pre_opcionales:
        query=query & (db.mod_pre_atr.opcional==True) #& (db.mod_atr.grp_atr.belongs(ATR_ESPECIAL.GRUPO_PRIMARIO,ATR_ESPECIAL.GRUPO_SECUNDARIO))
    else: #aqui hay que evitar las opcionales de mod_tipo raiz y que no sean primarias,secundarias o salida
        query = query & ((db.mod_pre_atr.opcional == False) | ((db.mod_pre_atr.opcional == True) & (db.mod_atr.grp_atr.belongs(ATR_ESPECIAL.GRUPO_PRIMARIO,ATR_ESPECIAL.GRUPO_SECUNDARIO))))
    if not session.pre_detalle:
        query = query & (db.mod_pre_atr.mod_tipo == IDRAIZ_MOD_TIPO)

    left=[db.mod_atr.on(db.mod_pre_atr.atr==db.mod_atr.id),db.mod_grp_atr.on(db.mod_grp_atr.id==db.mod_atr.grp_atr),db.mod_tipos.on(db.mod_tipos.id==db.mod_pre_atr.mod_tipo)]
    fields=[db.mod_pre_atr.mod_tipo,db.mod_pre_atr.atr,db.mod_pre_atr.valor]
    db.mod_pre_atr.pre.default=request.vars.pre_id
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults.copy() if request.extension=='pdf' else GRAL.grid_defaults.copy()
    defaults['paginate']=200
    defaults['selectable'] = lambda ids: redirect(URL(request.function, vars=request._get_vars)) #necesario para que salga el boton submit de envio
    defaults['editable']=defaults['deletable'] = defaults['create']=False
    #if 'edit' in request.args: #esto es para editar en linea
    #    options_mod_pre_atr(db,request.args[-1])
    db.mod_pre_atr.valor.requires=None #si hace falta, hacer la validadcion de cada valor en basic_custom   .myFormValidation
    frmkey='gridpreatrdata'
    db.mod_pre_atr.valor.listable = True
    db.mod_pre_atr.valor.represent = lambda v, r: options_widget_mod(db.mod_pre_atr.valor, v, r,
                                                                     **{'_name': 'valor_row_%s' % r['id'],
                                                                        '_class': 'generic-widget form-control'})

    if len(request.post_vars)> 0:
        if request.post_vars._formname==frmkey:
            for key, value in request.post_vars.items():
                (field_name, sep, row_id) = key.partition('_row_')  # name looks like home_state_row_99
                if row_id:
                    db(db.mod_pre_atr.id == row_id).update(**{field_name: value})
    grid = SQLFORM_plus(query,user_signature=False, links=[], fields=fields, left=left, formname=frmkey,title=db.mod_pre_atr._plural,searchable=False,field_id=db.mod_pre_atr.id, orderby=[db.mod_tipos.lft,db.mod_atr.orden_descripcion,db.mod_atr.name], **defaults)()
    grid['grid'].elements(_type='checkbox', _name='records', replace=None)  # remove selectable's checkboxes
    agrupa_columna(grid['grid'],1)
    js='web2py_component("%s",'
    bt = grid['grid'].element('.web2py_console div').components.append(form)
    #grid_addbutton(grid, "Inicializar atributos", URL('grid_pre_atr_rec', vars=dict(pre_id=request.vars.pre_id), user_signature=True),confirm_txt='¿Generar atributos desde configuración y volver a valores por defecto?')
    url=URL(f=request.function, args=(request.vars.pre_id),vars=dict(pre_id=request.vars.pre_id))
    grid_addbutton_self(grid, "Inicializar atributos",url,
                    confirm='¿Calcular Atributos por defecto? TODAS LAS SELECCIONES HECHAS SE ANULARÁN')
    return grid


@auth.requires_login()
def grid_pre_atr():
    filtra_lista_request_vars(request.vars,'pre_id')
    query=((db.mod_pre_atr.pre==request.vars.pre_id)&(db.mod_pre_atr.subnave==0))
    frmkey = 'gridpreatrdata'
    if len(request.args) >0 and '_formname' not in  request.vars: #compruebo si viene _formname porque cunado viene del botón no hay formname, cuando viene de submit por cambio de checks sí,
        #ya que no hay forma de desahacerse de los args pues los propaga en el el redirect cuando viene del callback del botón,
        if request.args(-1):
            recolectar_atributos_presupuesto(db, request.args(-1))
            session.flash = 'Variables calculadas!!!'
            url = URL(request.funcion, args=[], vars=dict(pre_id=request.args(-1)))
            redirect(url)
    else:
        inicial=(db(query).count() == 0)
        if len(request.post_vars) > 0:
            if request.post_vars._formname == frmkey:
                for key, value in request.post_vars.items():
                    (field_name, sep, row_id) = key.partition('_row_')  # name looks like home_state_row_99
                    if row_id:
                        #TODO Esto hay que averiguar el tipo del atributo y hacer el requires adecuado.
                        tipo=db.mod_pre_atr(row_id)
                        if tipo:
                            tipo=tipo.tipo
                            if tipo==MOD_ATR_TIPO.formula:
                                db.mod_pre_atr.valor.requires = IS_DECIMAL_IN_RANGE(dot=',')
                            #elif tipo==MOD_ATR_TIPO.vector:
                            #    db.mod_pre_atr.valor.requires = IS_MY_LIST() #ESTE VALIDADOR EN PRODUCCION NO FUNCIONA BIEN. LE AÑDE FORMATO DE STRINGS CADA VEZ CADA VEZ MAS
                            else:
                                db.mod_pre_atr.valor.requires = None
                            resp=db(db.mod_pre_atr.id == row_id).validate_and_update(**{field_name: value})
                            if resp.errors:
                                response.flash=resp.errors
                        pass
        else:
            recolectar_atributos_presupuesto(db, request.vars.pre_id,inicial=inicial)
    form = FORM(SPAN(INPUT(_name="opcionales", _id='pre_opcionales',_type='checkbox', value=True if session.pre_opcionales else False,
                           _onchange='$("form[name=frmsel]").submit();'), LABEL('Atrib. de diseño',_for='pre_opcionales'),_class='col-sm-2'),
                SPAN(INPUT(_name="detalle", _id='pre_detalle',_type='checkbox', value=True if session.pre_detalle else False,
                           _onchange='$("form[name=frmsel]").submit();'), LABEL('Ubicaciones',_for='pre_detalle'),_class='col-sm-2'),
                _name="frmsel")
    if form.accepts(request.vars,formname='frmsel',keepvalues=True):
        session.pre_opcionales = form.vars.opcionales
        session.pre_detalle = form.vars.detalle

    if not session.pre_opcionales:
        query=query & (db.mod_pre_atr.opcional==True) #& (db.mod_atr.grp_atr.belongs(ATR_ESPECIAL.GRUPO_PRIMARIO,ATR_ESPECIAL.GRUPO_SECUNDARIO))
    else: #aqui hay que evitar las opcionales de mod_tipo raiz y que no sean primarias,secundarias o salida
        query = query & ((db.mod_pre_atr.opcional == False) | ((db.mod_pre_atr.opcional == True)))
    if not session.pre_detalle:
        query = query & (db.mod_pre_atr.mod_tipo == IDRAIZ_MOD_TIPO)
    db.mod_pre_atr.mod_tipo.label='Ubicación'
    left=[db.mod_atr.on(db.mod_pre_atr.atr==db.mod_atr.id),db.mod_grp_atr.on(db.mod_grp_atr.id==db.mod_atr.grp_atr),db.mod_tipos.on(db.mod_tipos.id==db.mod_pre_atr.mod_tipo)]
    fields=[db.mod_pre_atr.atr,db.mod_pre_atr.valor,db.mod_pre_atr.mod_tipo]
    db.mod_pre_atr.pre.default=request.vars.pre_id
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults.copy() if request.extension=='pdf' else GRAL.grid_defaults.copy()
    defaults['paginate']=200
    defaults['selectable'] = lambda ids: redirect(URL(request.function, vars=request._get_vars)) #necesario para que salga el boton submit de envio
    defaults['editable']=defaults['deletable'] = defaults['create']=False
    #if 'edit' in request.args: #esto es para editar en linea
    #    options_mod_pre_atr(db,request.args[-1])
    db.mod_pre_atr.valor.requires=None #si hace falta, hacer la validadcion de cada valor en basic_custom   .myFormValidation
    db.mod_pre_atr.valor.listable = True
    db.mod_pre_atr.valor.represent = lambda v, r: options_widget_mod(db.mod_pre_atr.valor, v, r,
                                                                     **{'_name': 'valor_row_%s' % r['id'],
                                                                        '_class': 'generic-widget form-control'})

    grid = SQLFORM_plus(query,user_signature=False, links=[], fields=fields, left=left, formname=frmkey,title=db.mod_pre_atr._plural,
                        searchable=False,field_id=db.mod_pre_atr.id, orderby=[db.mod_atr.orden_descripcion,db.mod_atr.name,db.mod_tipos.lft], **defaults)()
    grid['grid'].elements(_type='checkbox', _name='records', replace=None)  # remove selectable's checkboxes
    agrupa_columna(grid['grid'],1)
    js='web2py_component("%s",'
    bt = grid['grid'].element('.web2py_console div').components.append(form)
    #grid_addbutton(grid, "Inicializar atributos", URL('grid_pre_atr_rec', vars=dict(pre_id=request.vars.pre_id), user_signature=True),confirm_txt='¿Generar atributos desde configuración y volver a valores por defecto?')
    url=URL(f=request.function, args=(request.vars.pre_id),vars=dict(pre_id=request.vars.pre_id))
    grid_addbutton_self(grid, "Inicializar atributos",url,
                    confirm='¿Calcular Atributos por defecto? TODAS LAS SELECCIONES HECHAS SE ANULARÁN')
    return grid



@auth.requires_login()
def grid_inver():
    inver=Invernadero(db,request.vars.pre_id)()
    """
    Ejemplos:
    Suma de elementos en un diccionario: 'reduce(lambda x,y: x+y,[v for k,v in {_seg_frn_ext}.items()])'

    """
    #form,error=IS_FORMULA(db,db.mod_atr.clave)('sumv(@_trm_cor_frn["9.6"][v])')
    form,error=IS_FORMULA(db,db.mod_atr.clave)('@_canales.med.sbj[6]')
    a = Formula(inver.atr)
    res = a(form)
    inver.atr.add(value=res if not a.error else a.error,id='200')
    inver.atr.set_context(0,1)
    inver.salva_atr() #TODO Reviar qué se guarda y para qué.
    subnave=db(db.mod_pre_subnaves.pre==request.vars.pre_id).select(orderby=~db.mod_pre_subnaves.tund).first()
    if subnave:
        subnave=subnave.id
    inver.atr.set_context(subnave) #TODO Desplegable en la vista para ver los atributos de cada grupo de naves
    return dict(inver=inver,ATRS=ATRS)

@auth.requires_login()
def grid_pre_mod_calc():
    inver = Invernadero(db, request.vars.pre_id)()
    inver.calcula_kits()
    redirect (URL('grid_pre_mod',vars=request.vars))

@auth.requires_login()
def grid_pre_pie_calc():
    inver = Invernadero(db, request.vars.pre_id)()
    inver.calcula_piezas()
    redirect(URL('grid_pre_pie', vars=request.vars))
