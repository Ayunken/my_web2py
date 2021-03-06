# -*- coding: utf-8 -*-
import gluon.contenttype
from plugin_jstree import JsTree
import datetime
from plugin_selectplus import multiTab_widget, SelectTreeWidget
from basic import windows_popup_load, grid_addbutton_self
import os,copy
#funciones para llamar a cerrar la ventana de dialogo que selectplus abre por una funcion diferente de la estandar
from plugin_selectplus import *
if False:
    from ..models.custom import *
    from ..models.basic_custom import *
    from ..models._kit import *
    from ..models.db import *
    from ..models.invernadero import *
def index(): return dict(message="hello from mod.py")

@auth.requires_login()
def mod_tipos():
    ### inject the mptt tree model to the jstree plugin ###
    divmod='divmodulos'
    url=URL(f='grid_mod_tipo.load',vars=dict(mod_tipo_id='node_id'),user_signature=True)
    jstree = JsTree(tree_model=mptt, renderstyle=True, version=3, search=True,selectcomponent=[url,divmod],
                    keyword='jstree_tipmod',count_descendants=True)
    if not mptt.roots().count():
        _root1 = mptt.insert_node(None, name='/', node_type='root')
    title=db.mod_tipos._plural
    query=db.mod_tipos
    grid=DIV(_id=divmod,_class='col-md-8')
    j=jstree()
    return dict(title=title,arbol=DIV(j,_class='col-md-4'),grid=grid)

@auth.requires_login()
def mod_tipos2():
    ### inject the mptt tree model to the jstree plugin ###
    divmod='divmodulos'
    response.view='mod/mod_tipos.%s' % request.extension
    url=URL(f='grid_mod_tipo2.load',vars=dict(mod_tipo2_id='node_id'),user_signature=True)
    jstree = JsTree(tree_model=mptt2, renderstyle=True, version=3, search=True,selectcomponent=[url,divmod],
                    keyword='jstree_tipmod2',count_descendants=True)
     ### populate records ###########################################################
    if not mptt2.roots().count():
        _root1 = mptt2.roots.insert_node(None, name='raiz', node_type='root')
   
    title=db.mod_tipos2._plural
    query=db.mod_tipos2
    grid=DIV(_id=divmod,_class='col-md-8')
    j=jstree()
    return dict(title=title,arbol=DIV(j,_class='col-md-4'),grid=grid)


@auth.requires_login()
def grid_mod_cmp():
    filtra_lista_request_vars(request.vars, 'mod_id')
    query=db(db.mod_cmp.mod==request.vars.mod_id)
    rq=request
    db.mod_cmp.mod.default=request.vars.mod_id
    db.mod_cmp.mod.readable=db.mod_cmp.mod.writable=False
    #response.view='grid.%s' % request.extension
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    left = [db.mod_mod_pie.on((db.mod_mod_pie.tipo == db.mod_cmp.cmp_tipo) & (
        (db.mod_mod_pie.id == db.mod_cmp.cmp_mod) | (db.mod_mod_pie.id == db.mod_cmp.cmp_pie)))]
    fields = [db.mod_cmp.cmp_mod,db.mod_cmp.cmp_tipo, db.mod_mod_pie.codigo, db.mod_mod_pie.name, db.mod_cmp.formula]
    widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='cmpmod',  id_field=db.mod.id, min_length=1)
        ###IMPORTANTE: SI LE PONES FORMNAME AL GRID COMO GRID_FORM (GUIONES) CASA EL JAVASCRITP  ERROR
    ## NUMERIC SEPARATOR NOSE QUE TRAS LITERAL
    #widget=SelectOrAddOption( db.mod, select_id='no_table_copymod')
    form = SQLFORM.factory(
        Field('copymod', 'integer',label='Copiar componentes desde ', requires=IS_NULL_OR(IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name)) ,widget=widget),_name='copymod')
    form.element(_type='submit')['_value']=T('Copiar')
    if form.process(formname='copymod').accepted:
        row=db(db.mod_cmp.mod==form.vars.copymod).select()
        if row:
            for i in row:
                i.mod=request.vars.mod_id
                del(i.id)
                db.mod_cmp.insert(**i)
        response.flash = 'Componentes copiados'
    elif form.errors:
        response.flash = 'form has errors'
    formcopy={'table':db.mod_cmp,'copy': False, 'delete':True}
    if len(request.args)==0:
        links = [lambda row: A('', _title='Componentes en ventana', _onclick='openform_modcmp(%(mod_cmp.cmp_mod)s,"%(mod_mod_pie.name)s - componentes");' % row,
                           _class='btn btn-default btn-secondary glyphicon glyphicon-list') if row['mod_cmp.cmp_tipo']== MOD_CMP_TIPO.modulo else None,
                 lambda row: A('', _title='Atributos en ventana', _onclick='openform_modatr(%(mod_cmp.cmp_mod)s,"%(mod_mod_pie.name)s - atributos");' % row,
                               _class='btn btn-default btn-secondary glyphicon glyphicon-tasks') if row['mod_cmp.cmp_tipo']== MOD_CMP_TIPO.modulo else None]
    else:
        links=None
    grid = SQLFORM_plus(query, links=links, fields=fields, left=left, field_id=db.mod_cmp.id, formcopy=formcopy,title='Componentes', **defaults)
    if request.extension=='pdf':
        return grid()
    else:
        gridp=grid()
        gridobj = gridp['grid']
        gridobj.components.extend([windows_popup_load('modcmp', 'grid_mod_cmp0', 'mod_id')])  # ventanita emergente con componentes
        gridobj.components.extend([windows_popup_load('modatr', 'grid_mod_atr0', 'mod_id')])
        return dict(formcopia=form,**gridp)


@auth.requires_login()
def grid_mod_cmp0():
    filtra_lista_request_vars(request.vars, 'copymod')
    if 'copymod' in request.vars:
        id=request.vars.copymod
    else:
        filtra_lista_request_vars(request.vars, 'mod_id')
        id=request.vars.mod_id
    query=db(db.mod_cmp.mod==id)
    response.view='grid.%s' % request.extension
    defaults=gral.grid_defaults
    left = [db.mod_mod_pie.on((db.mod_mod_pie.tipo == db.mod_cmp.cmp_tipo) & (
        (db.mod_mod_pie.id == db.mod_cmp.cmp_mod) | (db.mod_mod_pie.id == db.mod_cmp.cmp_pie)))]
    fields = [db.mod_mod_pie.codigo, db.mod_mod_pie.name, db.mod_cmp.formula]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False,left=left, field_id=db.mod_cmp.id, title='Componentes')
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None)
    return dict(**gridp)

@auth.requires_login()
def grid_mod_atr0():
    filtra_lista_request_vars(request.vars, 'copymod')
    if 'copymod' in request.vars:
        id=request.vars.copymod
    else:
        filtra_lista_request_vars(request.vars, 'mod_id')
        id=request.vars.mod_id
    query=db(db.mod_mod_atr.mod==id)
    left = [db.mod_atr.on((db.mod_mod_atr.atr == db.mod_atr.id))]
    response.view='grid.%s' % request.extension
    defaults=gral.grid_defaults
    fields = [db.mod_atr.name, db.mod_atr.grp_atr, db.mod_mod_atr.rango, db.mod_mod_atr.val_def, db.mod_mod_atr.lock]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False, left=left,field_id=db.mod_mod_atr.id, title='Atributos')
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None)
    return dict(**gridp)

@auth.requires_login()
def grid_mod_pie():
    filtra_lista_request_vars(request.vars, 'mod_id')
    query=db(db.mod_pie_fin.mod==request.vars.mod_id)
    #left=[db.productos.on(db.productos.id==db.mod_cmp.cmp_pie),db.mod.on(db.mod.id==db.mod_cmp.cmp_mod)]
    rq=request
    response.view='grid.%s' % request.extension
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    formname='mod_pie_%s' % request.vars.mod_id
    left = [db.mod_pie_fin.on(db.mod_pie_fin.cmp_pie == db.productos.id)]
    fields = [db.productos.codigo, db.productos.name,db.mod_pie_fin.nivel,db.mod_pie_fin.formula,db.mod_pie_fin.cantidad]
    grid = SQLFORM_plus(query, links=[],fields=fields, left=left, title='Piezas finales', editable=False,deletable=False,orderby=[db.mod_pie_fin.nivel,db.productos.codigo],formname=formname, **defaults)
    gridp=grid()
    grid_addbutton_self( gridp, "Calcular piezas finales",URL('grid_mod_pie_calculate.%s' % request.extension, vars=dict(mod_id=request.vars.mod_id)),confirm=True)
    return dict(**gridp)


@auth.requires_login()
def grid_mod_pie_calculate():
    piezas=mod_desarrolla_piezas(request.vars.mod_id)
    for k,v in piezas.items():
        db.mod_pie_fin.insert(mod= request.vars.mod_id,**v)
    return grid_mod_pie()


@auth.requires_login()
def grid_mod_mod_atr0():
    filtra_lista_request_vars(request.vars, 'copyatrmod')
    query=db(db.mod_mod_atr.mod==request.vars.copyatrmod)
    response.view='grid.%s'%request.extension
    left=[db.mod_atr.on((db.mod_mod_atr.atr==db.mod_atr.id))]
    fields=[db.mod_atr.name,db.mod_atr.grp_atr,db.mod_mod_atr.rango,db.mod_mod_atr.val_def,db.mod_mod_atr.lock]
    defaults=gral().grid_pdf_defaults if request.extension=='pdf' else gral().grid_defaults
    grid=SQLFORM_plus(query,links=[],fields=fields,left=left, editable=False, deletable=False, csv=False,create=False, searchable=False, field_id=db.mod_mod_atr.id,title='Atributos',**defaults)
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None) #quitamos contador de regisros
    return dict(**gridp)


@auth.requires_login()
def grid_mod_mod_atr():
    filtra_lista_request_vars(request.vars, 'mod_id')
    query=db(db.mod_mod_atr.mod==request.vars.mod_id)
    db.mod_mod_atr.mod.default=request.vars.mod_id
    db.mod_mod_atr.mod.writable=False
    left=[db.mod_atr.on((db.mod_mod_atr.atr==db.mod_atr.id))]
    fields=[db.mod_atr.name,db.mod_atr.grp_atr,db.mod_mod_atr.rango,db.mod_mod_atr.val_def,db.mod_mod_atr.lock]
    response.view='%s/grid_mod_atr.%s' % (request.controller,request.extension)
    defaults=gral().grid_pdf_defaults if request.extension=='pdf' else gral().grid_defaults
    widget=AutocompleteWidgetSelectOrAddOption(request, db.mod.name,keyword='atrmod',  id_field=db.mod.id, min_length=1)
    ###IMPORTANTE: SI LE PONES FORMNAME AL GRID COMO GRID_FORM (GUIONES) CASA EL JAVASCRITP  ERROR
    ## NUMERIC SEPARATOR NOSE QUE TRAS LITERAL
    #widget=SelectOrAddOption( db.mod, select_id='no_table_copymod')

    form = SQLFORM.factory(
        Field('copyatrmod', 'integer',label='Copiar atributos desde ', requires=IS_NULL_OR(IS_IN_DB(db,db.mod,'%(name)s',orderby=db.mod.name)) ,widget=widget),_name='copyatr')
    form.element(_type='submit')['_value']=T('Copiar')
    
    if form.process(formname='copyatr').accepted:
        row=db(db.mod_mod_atr.mod==form.vars.copyatrmod).select()
        if row:
            for i in row:
                i.mod=request.vars.mod_id
                del(i.id)
                db.mod_mod_atr.insert(**i)
        response.flash = 'Atributos copiados'
    elif form.errors:
        response.flash = 'form has errors'
    formcopy={'table':db.mod_mod_atr,'copy': False, 'delete':True}
    grid=SQLFORM_plus(query,links=[],fields=fields,left=left, field_id=db.mod_mod_atr.id,title='Atributos',formcopy=formcopy,**defaults)
    gridp=grid()
    return dict(formcopia=form,**gridp)


@auth.requires_login()
def grid_mod_mod():
    filtra_lista_request_vars(request.vars, 'mod_id')
    query=db(db.mod_mod.cmp_mod==request.vars.mod_id)
    #left=[db.productos.on(db.productos.id==db.mod_cmp.cmp_pie),db.mod.on(db.mod.id==db.mod_cmp.cmp_mod)]
    rq=request
    response.view='grid.%s' % request.extension
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    formname='mod_pie_%s' % request.vars.mod_id
    left = [db.mod.on(db.mod_mod.mod == db.mod.id)]
    fields = [db.mod.name,db.mod_mod.nivel,db.mod_mod.cantidad]
    grid = SQLFORM_plus(query, links=[],fields=fields, left=left, title='Dónde se utiliza', editable=False,deletable=False,orderby=[db.mod_mod.nivel,db.mod.name],formname=formname, **defaults)
    return grid()



@auth.requires_login()
def view_mod_tabs0(form,botones):
    reg=db.mod(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], [T('Componentes'),dict(f='grid_mod_cmp.load', vars=dict(mod_id=reg.id),user_signature=True)],[T('Atributos'),dict(f='grid_mod_mod_atr.load',vars=dict(mod_id=reg.id),user_signature=True)],[T('dónde se utiliza'),dict(f='grid_mod_mod.load',vars=dict(mod_id=reg.id),user_signature=True)],[T('Piezas'),dict(f='grid_mod_pie.load',vars=dict(mod_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod._singular,tablename='mod')


@auth.requires_login()
def view_mod_tabs():
    tabla=db.mod
    back_f='grid_mod'
    formname='form_%s' % tabla._tablename
    if len(request.args)<4: #esto indicaría que no está en una ventana de un select_add/edit
        botones=botones_back(request,f=back_f)
    else: botones=''
    if 'new' in  request.args:
        form =SQLFORM(tabla,_name=formname) # add
        response.view='grid.%s' % request.extension
        if len(request.args)==3:
            botones=''
            selectaddplus_close_dialog(response,request,form,db)
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form,botones=botones,title='Nuevo %s' % tabla._singular)
    else:
        if len(request.args)>1:
            form =SQLFORM(tabla, request.args[-1],_name=formname) # edit/update/change
            if len(request.args)==4: #esto es que se está en una ventana de dialogo uI
                selectaddplus_close_dialog(response,request,form,db)
            elif form.process(formname=formname).accepted:
                redirect(URL(back_f))
            return view_mod_tabs0(form,botones)
        else:
            session.flash=T('%s no existe') % (tabla._singular)
            redirect(URL(back_f))


@auth.requires_login()
def grid_mod_tipo():
    filtra_lista_request_vars(request.vars, 'mod_tipo_id')
    db.mod_tipos.id.readable=False
    form = SQLFORM(db.mod_tipos, record=request.vars.mod_tipo_id,fields=['abreviatura'],_name='form_mod_tipos')
    if form.process().accepted:
        response.flash = 'abreviatura cambiada'
    db.mod.tipo.default=request.vars.mod_tipo_id
    raiz = db.mod_tipos[request.vars.mod_tipo_id]
    # query=mptt.descendants_from_node(request.vars.mod_tipo_id,include_self=True)(db.mod_tipos.id)
    grid=grid_mod0(db.mod.tipo.contains(request.vars.mod_tipo_id))
    if len(request.args) > 1 and not 'new' in request.args:
        return grid
    else:
        response.view='mod/grid_mod_tipo.load'
        return dict( formulario=form,**grid)


@auth.requires_login()
def grid_mod_tipo2():
    filtra_lista_request_vars(request.vars, 'mod_tipo2_id')
    db.mod_tipos2.id.readable=False
    form = SQLFORM(db.mod_tipos2, record=request.vars.mod_tipo2_id,fields=['abreviatura'],_name='form_mod_tipos')
    if form.process().accepted:
        response.flash = 'abreviatura cambiada'
    db.mod.tipo2.default=request.vars.mod_tipo2_id
    raiz=db.mod_tipos2[request.vars.mod_tipo2_id]

    grid=grid_mod0(mptt2.descendants_from_node(request.vars.mod_tipo2_id, include_self=True)( db.mod.tipo2 == db.mod_tipos2.id))
    if len(request.args) > 1 and not 'new' in request.args:
        return grid
    else:
        response.view='mod/grid_mod_tipo.load'
        return dict( formulario=form,**grid)


@auth.requires_login()
def piezas():
    query=db(db.productos.origen.belongs(700,702))
    response.view='grid.%s' % request.extension
    #fields=[db.productos.codigo,db.productos.name]
    fields=[db.productos[f] for f in ('codigo','name','kg_real','cod_uni')]
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    #defaults['details']=False
    links=[]#[lambda row: A('View',_href=URL('view_client',vars=dict(idc=row.id),user_signature=True),_class='btn btn-default')]
    grid=SQLFORM_plus(query,links=links,fields=fields,title='Piezas',**defaults)
    if len(request.args)>1 and not 'new' in request.args:
        return view_pie_tabs0(grid.grid,botones_back(request,f=request.function))
    else:
    #si estamos en una ventana, y se ha dado de alta, pasamos a la vista edit
        return grid()

    

@auth.requires_login()
def view_pie_tabs0(form,botones):
    reg=db.productos(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], [T('Atributos'),dict(f='grid_pie_atr.load',vars=dict(pie_id=reg.id),user_signature=True)],[T('dónde se utiliza'),dict(f='grid_pie_mod.load',vars=dict(pie_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.productos._singular,tablename='productos')

def view_pie_tabs():
    tabla=db.productos
    back_f=request.url
    formname='form_%s' % tabla._tablename
    if len(request.args)<4: #esto indicaría que no está en una ventana de un select_add/edit
        botones=botones_back(request,f=back_f)
    else: botones=''
    if 'new' in  request.args:
        form =SQLFORM(tabla,_name=formname) # add
        response.view='grid.%s' % request.extension
        if len(request.args)==3:
            botones=''
            selectaddplus_close_dialog(response,request,form,db)
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form,botones=botones,title='Nuevo %s' % tabla._singular)
    else:
        if len(request.args)>1:
            form =SQLFORM(tabla, request.args[-1],_name=formname) # edit/update/change
            if len(request.args)==4: #esto es que se está en una ventana de dialogo uI
                selectaddplus_close_dialog(response,request,form,db)
            elif form.process(formname=formname).accepted:
                redirect(URL(back_f))
            return view_pie_tabs0(form,botones)
        else:
            session.flash=T('%s no existe') % (tabla._singular)
            redirect(URL(back_f))


@auth.requires_login()
def grid_pie_mod():
    filtra_lista_request_vars(request.vars, 'pie_id')
    query=db((db.mod_cmp.cmp_pie==request.vars.pie_id)&(db.mod_cmp.cmp_tipo=='P'))
    #left=[db.productos.on(db.productos.id==db.mod_cmp.cmp_pie),db.mod.on(db.mod.id==db.mod_cmp.cmp_mod)]
    rq=request
    response.view='grid.%s' % request.extension
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    formname='pie_mod_%s' % request.vars.pie_id
    left = [db.mod.on(db.mod_cmp.mod == db.mod.id)]
    fields = [db.mod.name,db.mod_cmp.formula]
    grid = SQLFORM_plus(query, links=[],fields=fields, left=left, title='Dónde se utiliza', deletable=False,orderby=[db.mod.name],formname=formname, **defaults)
    return grid()

@auth.requires_login()
def grid_pie_atr():
    filtra_lista_request_vars(request.vars, 'pie_id')
    query=db(db.mod_pie_atr.pieza==request.vars.pie_id)
    db.mod_pie_atr.pieza.default=request.vars.pie_id
    db.mod_pie_atr.pieza.writable=False
    left=[]#left=[db.mod_atr.on((db.mod_pie_atr.atr==db.mod_atr.id))]
    fields=[db.mod_pie_atr.atr,db.mod_pie_atr.val,db.mod_pie_atr.valor_especifico,db.mod_pie_atr.valorfinal]
    response.view='grid.%s' % request.extension
    defaults=gral().grid_pdf_defaults if request.extension=='pdf' else gral().grid_defaults
    formname='mod_pie_at_%s' % request.vars.pie_id
    grid=SQLFORM_plus(query,links=[],fields=fields,left=left, field_id=db.mod_pie_atr.id,title='Atributos',formname=formname,**defaults)
    return grid()

@auth.requires_login()
def grid_mod():
    return grid_mod0(db.mod)

def add_valor_atr_mod(query):
    return
    #añade un atributo a un conjunto de modulos (la query viene de grid_mod)
    set = (query)(db.mod.name.contains('CON ANCLAJE'))
    rows=set.select(db.mod.id)
    for m in rows:
        db.mod_mod_atr.insert(mod=m.id, atr=5,valores=[2],val_def=2,tipo='V' )


@auth.requires_login()
def grid_mod0(query,defecto=None):
    create=True
    left = []
    fields = [db.mod.name, db.mod.tipo,db.mod.tipo2]
    #if len(request.args)>1 :
    #    redirect(URL(r=request,f='view_mod_tabs',args=request.args,vars=request.vars,user_signature=True))
    if defecto:
        defaults=defecto
    else:
        defaults=gral.grid_pdf_defaults.copy() if request.extension=='pdf' else gral.grid_defaults.copy()

    if filtra_lista_request_vars(request.vars, 'mod_atr_id'):
        query=db((db.mod_mod_atr.atr==request.vars.mod_atr_id)  &  (db.mod.id==db.mod_mod_atr.mod))
        #left=[db.mod.on((db.mod_mod_atr.mod==db.mod.id))]
        create=False
        db.mod_mod_atr.atr.default=request.vars.mod_atr_id
    elif filtra_lista_request_vars(request.vars, 'rul_id'):
        patron=db.mod_rul(request.vars.rul_id).filtro_descripcion
        query=db(db.mod.name.like(patron))
        defaults['searchable']=False
        create=False
    else:
        fields = [db.mod.id]+ fields + [db.mod.um]
    defaults['orderby']=[db.mod.tipo]
    response.view='grid.%s' % request.extension
    links=[lambda row: A('',_title='Componentes en ventana',_onclick='openform_modcmp(%(id)s,"%(name)s - componentes");'%row,_class='btn btn-default btn-secondary glyphicon glyphicon-list'),
        lambda row: A('', _title='Atributos en ventana', _onclick='openform_modatr(%(id)s,"%(name)s - atributos");' % row,
                      _class='btn btn-default btn-secondary glyphicon glyphicon-tasks')]
    #opcion formcopy de plus

    formcopy={'fields':[Field('modname', 'string',label='Patrón nueva descripcion',default="%s.replace('buscar','sustituir')",comment="%s se sustituye en destino por la descripción del reg origen. Escribir cadenas entre comillas simples. Para unir cadenas usar símbolo +",requires=IS_NOT_EMPTY()),
            Field('chkcmp', 'boolean',label='Copiar Componentes',default=True),
            Field('chkatr', 'boolean',label='Copiar Atributos',default=True)],
             'callback':lambda ids: mod_copiar(ids)}
    formupd={'fields':[Field('modupdname', 'string',label='Patrón nueva descripcion',comment="%s se sustituye en destino por la descripción del reg origen. Escribir cadenas entre comillas simples. Para unir cadenas usar símbolo +",requires=IS_NOT_EMPTY()),
            Field('modupdtipo', 'list:reference db.mod_tipos',label='Establecer Ubicación',requires=IS_IN_DB(db(db.mod_tipos.parent>0),db.mod_tipos,'%(name)s',multiple=True,orderby=db.mod_tipos.name,zero=T('No cambiar')),widget=jschosen_widget_multiple),
            Field('modupdtipo2', db.mod_tipos2,label='Establecer Tipo',requires=IS_IN_DB(db(db.mod_tipos2.parent>0),db.mod_tipos2,'%(name)s',orderby=db.mod_tipos2.name,zero=T('No cambiar')),widget=jschosen_widget)],
             'callback':lambda ids: mod_upd(ids)}
    formadd={'form':SQLFORM(db.mod_mod_atr,fields=['atr','valores','val_def']), \
              'buttontext':T('Añadir atributo'),
              'callback': lambda ids,vars: mod_atr_add(ids,vars)}
    if 'rul_id' in request.vars:
        formcopy=None
    if False: #usar esto para manualmente hace cosas con kits
        add_valor_atr_mod(query)
    grid=SQLFORM_plus(query,links=links,field_id =db.mod.id,create=create,left=left,fields=fields,title=db.mod._plural,formcopy=formcopy,formupd=formupd,formadd=[formadd],**defaults)
    gridp=grid()
    if len(request.args)>1 and not 'new' in request.args:
        return view_mod_tabs0(grid.grid,botones_back(request,f=request.function))
    else:
        if not 'new' in request.args:
            gridobj=gridp['grid']
            gridobj.components.extend([windows_popup_load('modcmp','grid_mod_cmp0','mod_id')]) #ventanita emergente con componentes
            gridobj.components.extend([windows_popup_load('modatr', 'grid_mod_atr0', 'mod_id')])  # ventanita emergente con componentes
        return dict(**gridp)


@auth.requires_login()
def mod_copiar(ids):
    if ids:
        if request.vars.chkborrar:
            db(db.mod.id.belongs(ids)).delete()
            session.flash='Eliminados  %s kits'%(len(ids))
        else:
            for id in ids:
                mod=db.mod(id)
                if mod:
                    del mod.id
                    try:
                        mod.name_fix=eval(request.vars.modname % ("'%s'"%mod.name_fix))
                        mod.name = eval(request.vars.modname % ("'%s'" % mod.name))
                    except:
                        db.rollback()
                        session.flash='Error: %s. Se canceló toda la copia'%sys.exc_info()[0]
                        redirect(request.url)
                    res=db.mod.validate_and_insert(**mod)
                    if 'id' in res:
                        idnew=res['id']
                        if request.vars.chkcmp: #componentes
                            row=db(db.mod_cmp.mod==id).select()
                            if row:
                                for i in row:
                                    i.mod=idnew
                                    del(i.id)
                                    db.mod_cmp.insert(**i)
                        if request.vars.chkatr:#atributos
                            row=db(db.mod_mod_atr.mod==id).select()
                            if row:
                                for i in row:
                                    i.mod=idnew
                                    del(i.id)
                                    db.mod_mod_atr.insert(**i)
                    else:
                        db.rollback()
                        session.flash=res['error']
                        return
            session.flash='Copiados  %s kits'%(len(ids))
    else:
        session.flash='No seleccionó ningún registro'
    #redirect(request.url)


@auth.requires_login()
def mod_upd(ids):
    if ids:
        for id in ids:
            mod=db.mod(id)
            if mod:
                try:
                    if request.vars.modupdname:
                        mod.name_fix=eval(request.vars.modupdname % ("'%s'"%mod.name_fix))
                    if request.vars.modupdtipo:
                        if not isinstance(request.vars.modupdtipo,list):
                            mod.tipo = [request.vars.modupdtipo]
                        else:
                            mod.tipo=request.vars.modupdtipo
                    if request.vars.modupdtipo2:
                        mod.tipo2=request.vars.modupdtipo2
                except:
                    db.rollback()
                    session.flash='Error: %s. Se canceló toda la actualización'%sys.exc_info()[0]
                    redirect(request.url)
                mod.update_record()
            session.flash='Actualizados  %s kits'%(len(ids))
    else:
        session.flash='No seleccionó ningún registro'

@auth.requires_login()
def mod_atr_add(ids,vars):
    if ids:
        for id in ids:
            query = (db.mod_mod_atr.mod == id) & (db.mod_mod_atr.atr == vars.atr)
            if not vars.valores:
                db(query).delete()

            else:
                if not isinstance(vars.valores,list):
                    vars.valores=[vars.valores]
                if vars.val_def not in(vars.valores):
                        vars.val_def = vars.valores[0]
                resp=db.mod_mod_atr.update_or_insert(query, mod=id, atr=vars.atr, tipo=db.mod_atr(vars.atr).tipo,valores=vars.valores, val_def=vars.val_def)
                pass
                #except:
                #    db.rollback()
                #    session.flash = 'Error: %s. Se canceló toda la actualización' % sys.exc_info()[0]
                #    return
                    #redirect(request.url)                mod.update_record()
        session.flash = 'Añadido/actualizado el atributo en  %s kits' % (len(ids))
    else:
        session.flash = 'No seleccionó ningún registro'



@auth.requires_login()
def view_mod_rul_tabs0(form,botones):
    reg=db.mod_rul(request.args[-1])
    tabs=[T('Datos'),dict(f='view_mod_rul_edit.load',vars=request.vars,args=request.args,user_signature=True)], [T('Reglas'),dict(f='grid_mod_rul_lin.load', vars=dict(rul_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_rul._singular,tablename='mod_rul')


@auth.requires_login()
def view_mod_rul_edit():
    query=db.mod_rul
    response.view='mod_rul.%s' % request.extension
    fields=[db.mod_rul.name,db.mod_rul.filtro_descripcion]
    grid=SQLFORM(query,query(request.args[-1]))
    if grid.process().accepted:
        response.flash = T('Registro modificado')
    url=URL(c='mod',f='procesa_filtro',vars=dict(rul_id=request.args[-1]),user_signature=True)
    bt=BUTTON("Procesar Filtro",_onclick='if (confirm("¿Aplicar filtro a los kits resultantes?")) ajax("%s","",":eval");'%url)
    return dict(grid=grid,btprocesar=bt,reg=db.mod_rul(request.args[-1]))
    

@auth.requires_login()
def view_mod_rul_tabs():
    tabla=db.mod_rul
    back_f='grid_mod_rul'
    formname='form_%s' % tabla._tablename
    if len(request.args)<4: #esto indicaría que no está en una ventana de un select_add/edit
        botones=botones_back(request,f=back_f)
    else: botones=''
    if 'new' in  request.args:
        form =SQLFORM(tabla,_name=formname) # add
        response.view='grid.%s' % request.extension
        if len(request.args)==3:
            botones=''
            selectaddplus_close_dialog(response,request,form,db)
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form,botones=botones,title='Nuevo %s' % tabla._singular)
    else:
        if len(request.args)>1:
            form =SQLFORM(tabla, request.args[-1],_name=formname) # edit/update/change
            if form.process(formname=formname).accepted:
                redirect(URL(back_f))
            return view_mod_rul_tabs0(form,botones)
        else:
            session.flash=T('%s no existe') % (tabla._singular)
            redirect(URL(back_f))

@auth.requires_login()
def grid_mod_rul():
    query = db.mod_rul
    create=True
    left = []
    fields = [db.mod_rul.name, db.mod_rul.filtro_descripcion]
    defaults=gral().grid_pdf_defaults.copy() if request.extension=='pdf' else gral().grid_defaults.copy()
    defaults['orderby']=[db.mod_rul.name]
    response.view='grid.%s' % request.extension
    formcopy={'table': query}
    links=[lambda row: A('',_title='Componentes en ventana',_onclick='openform_modrul(%(id)s,"%(name)s");'%row,_class='btn btn-default btn-secondary glyphicon glyphicon-list')]
    grid=SQLFORM_plus(query,links=links,field_id =query.id,create=create,left=left,fields=fields,title=query._plural,formcopy=formcopy,**defaults)
    gridp=grid()
    if len(request.args)>1 and not 'new' in request.args:
        return view_mod_rul_tabs0(grid.grid,botones_back(request,f=request.function))
    else:
        if not 'new' in request.args:
            gridobj=gridp['grid']
            gridobj.components.extend([windows_popup_load('modrul','grid_mod_rul_lin0','rul_id')]) #ventanita emergente con componentes
        return dict(**gridp)

@auth.requires_login()
def grid_mod_rul_lin():
    filtra_lista_request_vars(request.vars, 'rul_id')
    query=db(db.mod_rul_lin.mod_rul==request.vars.rul_id)
    rq=request
    db.mod_rul_lin.mod_rul.default=request.vars.rul_id
    db.mod_rul_lin.mod_rul.readable=db.mod_rul_lin.mod_rul.writable=False
    #response.view='grid.%s' % request.extension
    defaults=gral.grid_pdf_defaults if request.extension=='pdf' else gral.grid_defaults
    mod_mod_pie2=db.mod_mod_pie.with_alias('mod_mod_pie2')
    left = [db.mod_mod_pie.on( ((db.mod_mod_pie.id == db.mod_rul_lin.cmp_pie_trg)| (db.mod_mod_pie.id == db.mod_rul_lin.cmp_mod_trg))  & (db.mod_rul_lin.tipo_trg==db.mod_mod_pie.tipo))]
    left += [mod_mod_pie2.on( ((mod_mod_pie2.id == db.mod_rul_lin.cmp_pie_tar) | (db.mod_mod_pie2.id == db.mod_rul_lin.cmp_mod_tar)) & (db.mod_rul_lin.tipo_tar==mod_mod_pie2.tipo))]
    fields = [db.mod_rul_lin.orden,db.mod_rul_lin.tipo_trg,db.mod_mod_pie.codigo, db.mod_mod_pie.name, db.mod_rul_lin.formula_trg, mod_mod_pie2.codigo, mod_mod_pie2.name,db.mod_rul_lin.formula_tar]
    widget=SelectOrAddOption(db.mod_rul,select_id='modrullin')
    ###IMPORTANTE: SI LE PONES FORMNAME AL GRID COMO GRID_FORM (GUIONES) CASA EL JAVASCRITP  ERROR
    ## NUMERIC SEPARATOR NOSE QUE TRAS LITERAL
    #widget=SelectOrAddOption( db.mod, select_id='no_table_copymod')
    form = SQLFORM.factory(
    Field('copyrul', 'integer',label='Copiar reglas desde ', requires=IS_NULL_OR(IS_IN_DB(db,db.mod_rul,'%(name)s',orderby=db.mod_rul.name)) ,widget=widget),_name='copyrul')
    form.element(_type='submit')['_value']=T('Copiar')
    if form.process(formname='copyrul').accepted:
        row=db(db.mod_rul_lin.mod_rul==form.vars.copyrul).select()
        if row:
            for i in row:
                i.mod_rul=request.vars.rul_id
                del(i.id)
                db.mod_rul_lin.insert(**i)
        response.flash = 'Reglas copiadas'
    elif form.errors:
        response.flash = 'form has errors'
    formcopy={'table':db.mod_rul_lin,'copy': False, 'delete':True}
    grid = SQLFORM_plus(query, links=[], fields=fields, left=left, field_id=db.mod_rul_lin.id, formcopy=formcopy,title='Líneas de Reglas', **defaults)
    if request.extension=='pdf':
        return grid()
    else:
        return dict(formcopia=form,**grid())


@auth.requires_login()
def grid_mod_rul_lin0():
    filtra_lista_request_vars(request.vars, 'copyrul')
    if 'copyrul' in request.vars:
        id=request.vars.copyrul
    else:
        filtra_lista_request_vars(request.vars, 'rul_id')
        id=request.vars.rul_id
    query=db(db.mod_rul_lin.mod_rul==id)
    response.view='grid.%s' % request.extension
    defaults=gral.grid_defaults
    left = [db.mod_mod_pie.on( (db.mod_mod_pie.id == db.mod_rul_lin.cmp_pie_trg) & (db.mod_mod_pie.tipo=='P'))]
    left += [db.productos.on( db.productos.id == db.mod_rul_lin.cmp_pie_tar )]
    fields = [db.mod_rul_lin.orden,db.mod_mod_pie.codigo, db.mod_mod_pie.name, db.productos.codigo,db.mod_rul_lin.formula_trg, db.productos.name,db.mod_rul_lin.formula_tar]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False,left=left, field_id=db.mod_rul_lin.id, title='Componentes')
    gridp=grid()
    gridp['grid'].elements('div.web2py_counter',replace=None)
    return dict(**gridp)


@auth.requires_login()
def grid_mod_rul_mod():
    filtra_lista_request_vars(request.vars, 'rul_id')
    patron=db.mod_rul(request.vars.rul_id).filtro_descripcion
    query=db((db.mod.name.like(patron))&(db.mod_cmp.cmp_pie==db.mod_rul_lin.cmp_pie_trg)&(db.mod_cmp.mod==db.mod.id)&(db.mod_rul_lin.mod_rul==request.vars.rul_id))
    fields =[db.mod.name]
    grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=100,details=False, editable=False,create=False,deletable=False, csv=False, searchable=False, field_id=db.mod.id, title='Kits afectados')
    response.view='grid.%s' % request.extension

@auth.requires_login()
def procesa_filtro():
    filtra_lista_request_vars(request.vars, 'rul_id')
    return 'alert("%s");'%modrul_lanza(db,request.vars.rul_id)
