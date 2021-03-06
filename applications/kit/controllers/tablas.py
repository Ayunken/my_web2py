# -*- coding: utf-8 -*-
if False:
    from gluon import *
    from db import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
import gluon.contenttype
from plugin_jstree import JsTree
import datetime
from plugin_selectplus import multiTab_widget, SelectTreeWidget
from basic import *


import os
#funciones para llamar a cerrar la ventana de dialogo que selectplus abre por una funcion diferente de la estandar
from plugin_selectplus import selectaddplus_close_dialog, AutocompleteWidgetSelectOrAddOption

@auth.requires_login()
def index(): return dict(message="hello from tablas.py")

@auth.requires_login()
def view_edit():
    from gluon.tools import Crud
    crud0 = Crud(current,db)
    crud0.settings.formstyle=myconf.get('forms.formstyle')
    response.view='grid.%s' % request.extension
    #grid=SQLFORM(query,record=db[tabla](request.vars.id))
    return dict(grid=crud0.update(request.args[0],request.args[1]))


@auth.requires_login()
def crud():
    #ESTO LIMITARLO EN UN FUTURO A UNA LISTA DE TABLAS, SINO POR AQUI HAY UNA PUERTA A EDITAR CUALQUIER TABLA
    if 'table' in request.vars and len(request.args)==0:
        tabla=request.vars.table
    elif len(request.args)>1:
        tabla=request.args[1]
    if not tabla:
        raise HTTP(400)
    else:
        if not(tabla in db):
            raise HTTP(400)
    response.view='grid.%s' % request.extension
    query=db[tabla]
    if tabla in report_fields_list(db):
        fields=report_fields_list(db)[tabla]
    else:
        fields=[db[tabla][f] for f in query.fields]
    title=db[tabla]._plural
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid=SQLFORM_plus(query,links=[],fields=fields,title=title,**defaults)
    return grid()



@auth.requires_login()
def mod_grp_atr():
    divmod='divatr'
    url=URL(f='grid_mod_atr.load',vars=dict(mod_grp_atr_id='node_id'),user_signature=True)
    jstree = JsTree(tree_model=mptt_atr, renderstyle=True, version=3, search=True,selectcomponent=[url,divmod])
    ### populate records ###########################################################
    if not mptt_atr.roots().count():
        _root1 = mptt_atr.roots.insert_node(None, name='raiz', node_type='root')
    title=db.mod_grp_atr._plural
    query=db.mod_grp_atr
    grid=DIV(_id=divmod,_class='col-md-9')
    #grid = LOAD(ajax=True,c='default',f='grid_mod.load',user_signature=True,_class='col-md-9',_id=divmod)
    return dict(title=title,arbol=DIV(jstree(),_class='col-md-3'),grid=grid)

@auth.requires_login()
def grid_atr_val():
    filtra_lista_request_vars(request.vars, 'mod_atr_id')
    query=db(db.mod_val.atr==request.vars.mod_atr_id)
    fields=[db.mod_val.name,db.mod_val.abreviatura, db.mod_val.valor]
    db.mod_val.atr.default=request.vars.mod_atr_id
    db.mod_val.atr.writable=False
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    response.view='grid.%s' % request.extension
    grid= SQLFORM_plus(query,links=[],fields=fields,title='Valores',orderby=db.mod_val.name,**defaults)
    return grid()

@auth.requires_login()
def grid_atr_val0(): #ejemplo de sql editable, para editar grids de pocos registros y no añadir
    tabla = db.mod_val
    query=db(tabla.atr==request.vars.mod_atr_id)
    fields = [db[tabla][f] for f in filter(lambda v: v!='atr', tabla.fields)]
    grid = SQLFORM_plus(query, maxtextlength=50, fields=fields,details=False, editable=False, create=False,
                        deletable=False, csv=False, searchable=False)
    gridp = grid()
    gridp['grid'].elements('div.web2py_counter', replace=None)
    response.view='grid.load'
    return gridp

@auth.requires_login()
def view_mod_atr_tabs():
    tabla=db.mod_atr
    back_f='grid_mod'
    formname='form_%s' % tabla._tablename
    from plugin_selectplus import selectaddplus_close_dialog
    if len(request.args)<4: #esto indicaría que no está en una ventana de un select_add/edit
        botones=botones_back(request,f=back_f)
    else: botones=''
    if 'new' in  request.args:
        form =SQLFORM(tabla,_name=formname) # add
        if len(request.args)==3:
            botones=''
            selectaddplus_close_dialog(response,request,form,db)
            response.view='grid.%s' % request.extension
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form,botones=botones,title='Nuevo %s' % tabla._singular)
    elif len(request.args)>1:
        form =SQLFORM(tabla, request.args[-1],_name=formname) # edit/update/change
        if len(request.args)==4: #esto es que se está en una ventana de dialogo uI
             selectaddplus_close_dialog(response,request,form,db    )
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return view_mod_atr_tabs0(form,botones)
    else:
        session.flash=T('%s no existe') % (tabla._singular)
        redirect(URL(back_f))


@auth.requires_login()
def view_mod_atr_tabs0(form,botones):
    reg=db.mod_atr(request.args[-1])
    tabs=[[T('Datos'),dict(content=form)], [T('Valores'),dict(c=request.controller,f='grid_atr_val.load',vars=dict(mod_atr_id=reg.id),user_signature=True)],
          [T('Módulos'),dict(c='mod',f='grid_mod.load',vars=dict(mod_atr_id=reg.id),user_signature=True)]]
    if reg.tipo!=MOD_ATR_TIPO.valores:
        del tabs[1]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_atr._singular,tablename='mod_atr')


@auth.requires_login()
def grid_mod_atr():
    vars=request.vars
    query = db.mod_atr
    if filtra_lista_request_vars ( request.vars,'mod_grp_atr_id'):
        raiz = db.mod_grp_atr(request.vars.mod_grp_atr_id)
        if raiz:  # si no tiene padre, no lo filtro, es el tipo raiz y con el muestro todos los modulos
            if raiz.parent:
                query = db(db.mod_atr.grp_atr == request.vars.mod_grp_atr_id)
                db.mod_atr.grp_atr.default = request.vars.mod_grp_atr_id
    filtra_lista_request_vars(request.vars, 'order')
    response.view='grid.%s' % request.extension

    if 'new' in request.args:
        for i in ['val_def']:
            db.mod_atr[i].writable=db.mod_atr[i].readable=False
    defaults = GRAL.grid_pdf_defaults.copy() if request.extension == 'pdf' else GRAL.grid_defaults.copy()
    links = [lambda row: A('', _title='Valores en ventana', _onclick='openform_atrval(%(id)s,"%(name)s");' % row,
                           _class='btn btn-default btn-secondary glyphicon glyphicon-list')]

    def modatr_upd(ids):
        tabla=db.mod_atr
        if ids:
            for id in ids:
                reg = tabla(id)
                if reg:
                    try:
                        if request.vars.modatrupdtipo:
                            reg.grp_atr = request.vars.modatrupdtipo
                    except:
                        db.rollback()
                        session.flash = 'Error: %s. Se canceló toda la actualización' % sys.exc_info()[0]
                        redirect(request.url)
                    reg.update_record()
                session.flash = 'Actualizados  {0} {1}'.format (len(ids),tabla._plural)
        else:
            session.flash = 'No seleccionó ningún registro'
            # redirect(request.url)

    formupd = {'fields': [Field('modatrupdtipo',db.mod_grp_atr, label='Establecer Grupo',
                                requires=IS_IN_DB(db(db.mod_grp_atr.parent > 0), db.mod_grp_atr, '%(name)s',
                                                  orderby=db.mod_grp_atr.name, zero=T('No cambiar')),
                                widget=jschosen_widget)],
               'callback': lambda ids: modatr_upd(ids)}

    if len(request.post_vars) > 0:
        for key, value in request.post_vars.items():
            (field_name, sep, row_id) = key.partition('_row_')  # name looks like home_state_row_99
            if row_id:
                if field_name[0:4] == 'inc-':
                    if value:
                        gridSorted_Incrementa(db.mod_atr.orden_descripcion,row_id,value)
                        break
                else:
                    db(db.mod_atr.id == row_id).update(**{field_name: value})

    editmode=False
    if 'order' in request.vars:
        if 'mod_atr.orden_descripcion' in request.vars.order:
            editmode=True
            defaults['selectable'] = lambda ids: redirect(
                URL(request.function, vars=request._get_vars))  # necesario para que salga el boton submit de envio
            defaults['editable'] = defaults['deletable'] = defaults['create'] = False
            db.mod_atr.orden_descripcion.represent = lambda v, r: field_sort_widget(db.mod_atr.orden_descripcion, v, r,orden=request.vars.order[0],
                                                                     **{'_name': 'orden_descripcion_row_%s' % r['id'],
                                                                        '_class': 'generic-widget form-control'})
    fields=report_fields_list(db)['mod_atr']
    #fields = [db[tabla][f] for f in ('id','name','clave','um','grp_atr','val_def','val_def_formula','rango','abreviatura','comments')]

    formcopy=formcopy={'table': query,
                       'fields':[Field('copy_name', 'string',label='Patrón nueva descripcion',
                                        default="'Copia de %s'",
                                        comment="%s se sustituye en destino por la descripción origen. Escribir cadenas entre comillas simples. Para unir cadenas usar símbolo +",
                                        requires=IS_NOT_EMPTY()),
                                 Field('copy_clave', 'string', label='Patrón nueva clave',
                                       default="'copy_%s'",
                                       requires=IS_NOT_EMPTY()),
                                  ]
            }
    grid = SQLFORM_plus(query, fields=fields, links=links, title=db.mod_atr._plural,  formcopy=formcopy,formupd=formupd,format='L', **defaults)
    gridp = grid()
    if editmode:
        gridp['grid'].elements(_type='checkbox', _name='records', replace=None)  # remove selectable's checkboxes
        bt = gridp['grid'].element('.web2py_table input', _type='submit')
        if bt:
            bt['_style'] = 'position: fixed; right: 1px; bottom: 60px;'  # boton de enviar en la parte izq.abajo
            bt['_class'] = 'ajax_btn btn btn-primary btn-default'  # y en color azul
    if len(request.args) > 1 and not 'new' in request.args:
        return view_mod_atr_tabs0(grid.grid, botones_back(request, f=request.function))
    else:
        if not 'new' in request.args:
            gridobj = gridp['grid']
            gridobj.components.extend(
                [windows_popup_load('atrval', 'grid_atr_val0', 'mod_atr_id')])  # ventanita emergente con componentes

        return gridp
