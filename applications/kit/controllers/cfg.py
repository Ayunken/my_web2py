# -*- coding: utf-8 -*-
import gluon.contenttype
from plugin_jstree import JsTree
import datetime
from plugin_selectplus import * #multiTab_widget, SelectTreeWidget
from basic import windows_popup_load,grid_addbutton
import os
#funciones para llamar a cerrar la ventana de dialogo que selectplus abre por una funcion diferente de la estandar
#from plugin_selectplus import  selectaddplus_close_dialog, AutocompleteWidgetSelectOrAddOption

if False:
    from gluon import *
    from db import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T


@auth.requires_login()
def index(): return dict(message="hello from cfg.py")


@auth.requires_login()
def grid_cfg():
    ### vista arbol de configuraciones###
    divmod='divcfgs'
    response.view='tree.{0}'.format(request.extension)
    url=URL(f='view_cfg_tabs.load',args=['edit','cfg_mod','node_id'],user_signature=True)
    jstree = JsTree(tree_model=mptt_cfg, renderstyle=True, version=3, search=True,selectcomponent=[url,divmod],
                    keyword='jstree_cfg_',count_descendants=True)
    if not mptt_cfg.roots().count():
        _root1 = mptt_cfg.insert_node(None, name='/', node_type='root')
    query=db.mod_cfg
    grid=DIV(_id=divmod,_class='col-md-9')
    j=jstree()
    return dict(title='Árbol de configuraciones',arbol=DIV(j,_class='col-md-3'),grid=grid)


@auth.requires_login()
def grid_cfg2():
    ### vista plana de configuraciones. no usada en principio###
    tabla=db.mod_cfg
    tabla2=db.mod_cfg.with_alias('cfg2')
    query = db.mod_cfg
    create=True
    if len(request.args) > 1 and not 'new' in request.args:
        return view_cfg_tabs()
    if filtra_lista_request_vars(request.vars,'mod_id'):
        query=db((db.mod_cfg_mod.mod==request.vars.mod_id)  &  (tabla.id==db.mod_cfg.cfg))
    fields=[tabla.id,tabla.name,tabla.comments]
    left=tabla2.on(tabla2.id==tabla.cfg_base)
    headers={tabla2.name: 'Config.Base'}
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    defaults['orderby']=[db.mod_cfg.orden]
    response.view = 'grid.%s' % request.extension
    grid = SQLFORM_plus(query, links=[], field_id=db.mod_cfg.id, create=create, headers=headers,left=left, fields=fields,
                        title=tabla._plural, **defaults)
    return grid()

@auth.requires_login()
def view_cfg_tabs(): #vista de ficha con pestañas sin grid previo
    tabla=db.mod_cfg
    reg=tabla(request.args[-1])
    if reg.id!=IDRAIZ_MOD_TIPO:
        cfgtip_propaga_hijos(reg.id)
    tabs=[T('Tipo de Kits'),dict(f='grid_mod_cfg_tip.load',vars=dict(cfg_id=reg.id),user_signature=True)], \
         [T('Atributos Base'), dict(f='grid_mod_cfg_atr.load', vars=dict(cfg_id=reg.id), user_signature=True)], \
         [T('Kits totales'), dict(f='grid_cfg_mod.load', vars=dict(cfg_id=reg.id), user_signature=True)], \
         [T('Observaciones'), dict(f='cfg_reg.load', args=request.args, user_signature=True)]
    tabs=multiTab_widget(tabs,tab_id="tabcfg")
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones='',tabs=tabs,title=tabla._singular,tablename='mod_cfg')

@auth.requires_login()
def cfg_reg(): #vista de ficha con pestañas sin grid previo
    tabla=db.mod_cfg
    reg=tabla(request.args[-1])
    for i in tabla.fields: #solo dejamos en la ficha el datos de comentarios
        if i not in ('id','comments','breve'):
            tabla[i].writable=tabla[i].readable=False
    formulario=SQLFORM(tabla,record=reg)
    if formulario.process().accepted:
        response.flash = 'Cambios guardados'
    elif formulario.errors:
        response.flash = 'el formulario tiene errores'
    response.view='grid.%s' % request.extension
    return dict(grid=formulario)


@auth.requires_login()
def grid_cfg_mod():
    filtra_lista_request_vars(request.vars, 'cfg_id')
    query=db.mod_cfg_mod.cfg==request.vars.cfg_id
    query=(query) & (db.mod_cfg_mod.mod==db.mod.id)
    jsadd=None
    if 'cfgtip_id' in request.vars:
        tip=db.mod_cfg_tip(request.vars.cfgtip_id)
        query = (db.mod_cfg_mod.cfg == tip.cfg)
        query= (query) & (db.mod_cfg_mod.mod_tipo==tip.mod_tipo)
    left=[]
    #left=[db.mod_tipos.on(db.mod_tipos.id==db.mod_cfg_mod.mod_tipo)]
    fields=[db.mod_cfg_mod.mod,db.mod_cfg_mod.mod_tipo,db.mod_cfg_mod.formula]
    db.mod_cfg_mod.cfg.default=request.vars.cfg_id
    db.mod_cfg_mod.cfg.readable=db.mod_cfg_mod.cfg.writable=False
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    if len(request.args)==0:
        links=[lambda row: A('',_title='Componentes en ventana',_onclick='openform_modcmp(%(id)s,"%(name)s - componentes");'%(db.mod(row.mod)), _class='btn btn-default btn-secondary glyphicon glyphicon-list'),
        lambda row: A('', _title='Atributos en ventana', _onclick='openform_modatr(%(id)s," %(name)s - atributos");' % (db.mod(row.mod)),
                           _class='btn btn-default btn-secondary glyphicon glyphicon-tasks')]
    else: links=None
    grid= SQLFORM_plus(query,links=links,fields=fields,left=left,title='Componentes',orderby=(db.mod_cfg_mod.mod_tipo,db.mod_cfg_mod.mod.name) , **defaults)()
    grid['grid'].components.extend([windows_popup_load('modcmp','grid_mod_cmp0','mod_id',c='mod')])
    grid['grid'].components.extend([windows_popup_load('modatr', 'grid_mod_atr0', 'mod_id', c='mod')])

    cambiado=False
    if jsadd:
        grid['grid'].components.extend([jsadd])
    """ ESTO SIRVE PARA RECARGAR LA PAGINA ENTERA DESDE UN AJAX COMPONENT O LOAD
    redirect(request.env.http_web2py_component_location, client_side=True)
    """

    if 'cfgtip_id' in request.vars:
        url = URL('cfg_genkits.%s' % request.extension, vars=dict(cfgtip_id=request.vars.cfgtip_id))
        grid_addbutton_self(grid, "Generar Kits", url)
    else:
        url=URL('cfg_genkits.%s' % request.extension,vars=dict(cfg_id=request.vars.cfg_id))
        grid_addbutton_self(grid,"Generar Todos Kits",url)
    return grid


@auth.requires_login()
def cfg_genkits():
    #calcular los kits de la configuración en base a atributos y tipos de kits de la plantilla
    cfgmod_genera_kits(db,idcfg=request.vars.cfg_id,idcfgtip=request.vars.cfgtip_id)
    session.flash = 'Kits calculados!!!'
    redirect(URL(f='grid_cfg_mod',vars=request.vars))



@auth.requires_login()
def grid_mod_cfg_atr():
    filtra_lista_request_vars(request.vars, 'cfg_id')
    qtip=db((db.mod_cfg_tip.cfg==request.vars.cfg_id) & (db.mod_cfg_tip.mod_tipo==IDRAIZ_MOD_TIPO)).select(db.mod_cfg_tip.id).first()
    if not qtip:
        request.vars.cfgtip_id=db.mod_cfg_tip.insert(cfg=request.vars.cfg_id,mod_tipo=IDRAIZ_MOD_TIPO)
    else:
        request.vars.cfgtip_id=qtip.id
    request.get_vars.cfgtip_id=request.vars.cfgtip_id
    return grid_cfg_tip_atr()
"""
    query=db(tabla.cfg_tip==idtip)

    tabla.cfg_tip.default=idtip
    tabla.cfg_tip.writable=False
    left=[db.mod_atr.on((tabla.atr==db.mod_atr.id))]
    fields=[db.mod_cfg_tip_atr.atr,db.mod_atr.grp_atr,tabla.rango,tabla.val_def ,tabla.lock]
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid = SQLFORM_plus(query, links=[], fields=fields, left=left, field_id=tabla.id, title='Atributos',
                        **defaults)()
    return grid

"""
@auth.requires_login()
def view_cfg_tip_tabs0(form,botones):
    reg=db.mod_cfg_tip(request.args[-1])
    tabs= [T('Atributos de Ubicación'), dict(f='grid_cfg_tip_atr.load', vars=dict(cfgtip_id=reg.id),user_signature=True)], \
          [T('Datos'),dict(content=form)], \
         [T('Kits de la ubicación'),dict(c='mod',f='grid_mod_tipo.load', vars=dict(mod_tipo_id=reg.mod_tipo.id),user_signature=True)], \
         [T('Kits filtrados'), dict(f='grid_cfg_tip_mod.load', vars=dict(cfgtip_id=reg.id,mod_tipo_id=reg.mod_tipo.id), user_signature=True)]
    reg['name']=reg.mod_tipo.name
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_cfg_tip._singular,tablename='mod_cfg_tip')

"""
@auth.requires_login()
def view_cfg_tip():
    tabla=db.mod_cfg_tip
    query = tabla
    create=True
    left=[]
    fields=[tabla.mod,tabla.mod_tipo,tabla.min,tabla.formula]
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    response.view = 'grid.%s' % request.extension
    grid = SQLFORM_plus(query, links=[], field_id=db.mod_cfg_tip.id, create=create, left=left, fields=fields,
                        title=tabla._plural, **defaults)
    if len(request.args) > 1 and not 'new' in request.args:
        return view_cfg_tip_tabs0(grid.grid, botones_back(request, f=request.function))
    else:
        return grid()
"""
@auth.requires_login()
def grid_mod_cfg_tip():
    filtra_lista_request_vars(request.vars,'cfg_id')
    tabla=db.mod_cfg_tip_combi
    query=(tabla.cfg_tip==db.mod_cfg_tip.id)&(tabla.cfg==request.vars.cfg_id)
    #left=[db.productos.on(db.productos.id==db.mod_cmp.cmp_pie),db.mod.on(db.mod.id==db.mod_cmp.cmp_mod)]
    left=[db.mod_tipos.on(db.mod_tipos.id==db.mod_cfg_tip.mod_tipo)]
    fields=[db.mod_cfg_tip.cfg,db.mod_tipos.name,db.mod_tipos.id,db.mod_cfg_tip.min_mods, db.mod_cfg_tip.formula,db.mod_tipos.level,db.mod_cfg_tip.tag]
    db.mod_cfg_tip.cfg.default=request.vars.cfg_id
    db.mod_cfg_tip.cfg.readable=db.mod_cfg_tip.cfg.writable=False
    db.mod_tipos.level.readable=False
    db.mod_cfg_tip.cfg.listable=False
    db.mod_tipos.id.listable=False
    db.mod_tipos.name.represent = lambda v, r: '%s%s' % ('*'*(r['mod_tipos.level']), v)
    response.view='grid.%s' % request.extension
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    defaults['user_signature'] = False
    def getlinkdel(row):
        if not row[db.mod_cfg_tip.tag]:
            if row[db.mod_tipos.id]!=IDRAIZ_MOD_TIPO:
                url=URL(args=('delete','mod_cfg_tip',row[db.mod_cfg_tip.id]),vars=request.vars,user_signature=True)
                return A('', _title='Eliminar',
          _href=url,
           delete='tr',
           callback=url,
            confirm=True,
          _class='btn btn-default btn-secondary glyphicon glyphicon-trash',cid=request.cid)
        else:
            return ''
    if len(request.args)==0:
        defaults['deletable'] = False
        links= [lambda row: A('', _title='Atributos en ventana',
                         _onclick='openform_cfgtipatr(%(mod_cfg_tip.id)s,"%(mod_tipos.name)s - atributos (%(mod_cfg_tip.id)s)");' % row,
                         _class='btn btn-default btn-secondary glyphicon glyphicon-tasks')]
        links.append(lambda row: getlinkdel(row))
    elif request.args[0]=='edit':
        links=[]
        db.mod_cfg_tip.mod_tipo.writable=False
        reg = db.mod_cfg_tip(request.args[-1])
        if reg.cfg != valNum(request.vars.cfg_id):
            request.args[-1]=db.mod_cfg_tip.insert(cfg=request.vars.cfg_id, mod_tipo=reg.mod_tipo,formula=reg.formula,min_mods=reg.min_mods)
            defaults['user_signature']=False
    else:
        links=[]
    grid= SQLFORM_plus(query,links=links,fields=fields,left=left,field_id=db.mod_cfg_tip.id,title=db.mod_cfg_tip._plural,orderby=[db.mod_tipos.lft],**defaults)()
    grid['grid'].components.extend([windows_popup_load('cfgtipatr', 'grid_cfg_tip_atr1', 'cfgtip_id')])

    if len(request.args) > 1 and not 'new' in request.args:
        return view_cfg_tip_tabs0(grid['grid'], botones_back(request, f=request.function))
    else:
        return grid

@auth.requires_login()
def grid_cfg_tip_atr1(): #en ventana solo lectura
    return grid_cfg_tip_atr0(False)

def grid_cfg_tip_atr(): #grid editar normal
    return grid_cfg_tip_atr0()

@auth.requires_login()
def grid_cfg_tip_atr0(editar=True):
    tabla=db.mod_cfg_tip_atr
    idvar = 'cfgtip_id'
    filtra_lista_request_vars(request.vars, idvar)
    id=request.vars[idvar]
    if id: #la llamada de lazy options viene sin idvar
        #metrodo por una consulta que busca los ascendentes y combina los atributos para solo tomar el de mayor nivel de profundidad
        query=(tabla.id==db.mod_cfg_tip_atr_combi.cfg_tip_atr)&(db.mod_cfg_tip_atr_combi.cfg_tip==id)
        query=query & (db.mod_cfg_tip.id==tabla.cfg_tip) & (db.mod_cfg_tip.mod_tipo==db.mod_tipos.id)
        #metodo sin combinar los atributos (los toma todos)
    #    padre = db.mod_cfg_tip(id)
    #    query =  (db.mod_cfg_tip.mod_tipo==db.mod_tipos.id) & (db.mod_cfg_tip.cfg==padre.cfg) & (db.mod_cfg_tip_atr.cfg_tip==db.mod_cfg_tip.id) & ((db.mod_cfg_tip_atr.lock==True) | (db.mod_cfg_tip_atr.cfg_tip==id))
    #    query=mptt.ancestors_from_node(padre.mod_tipo,include_self=True)(query)
    else:
        query=(tabla.id==0)
    left = [db.mod_atr.on((tabla.atr == db.mod_atr.id))]
    fields = [db.mod_cfg_tip.cfg,db.mod_cfg_tip_atr.cfg_tip,db.mod_tipos.name,db.mod_atr.name, db.mod_atr.grp_atr, tabla.rango, tabla.val_def,tabla.lock]
    tabla.cfg_tip.default=id
    tabla.cfg_tip.writable = False
    db.mod_cfg_tip_atr.cfg_tip.listable=False
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    defaults['user_signature'] = False
    response.view = 'grid.%s' % request.extension
    orden=[db.mod_tipos.level, db.mod_tipos.name, db.mod_atr.name]
    if editar:
        def getlinkdel(row):
            if row[db.mod_cfg_tip_atr.cfg_tip] == valNum(request.vars.cfgtip_id):
                url = URL(args=('delete', 'mod_cfg_tip_atr', row[db.mod_cfg_tip_atr.id]), vars=request.vars,
                              user_signature=True)
                return A('', _title='Eliminar',
                             _href=url,
                             delete='tr',
                             callback=url,
                             confirm='Eliminar atributo',
                             _class='btn btn-default btn-secondary glyphicon glyphicon-trash', cid=request.cid)
            else:
                return ''

        if len(request.args) == 0:
            defaults['deletable'] = False
            links=[lambda row: getlinkdel(row)]
            request.function = 'grid_cfg_tip_atr'
        elif 'edit' in request.args:
            reg = tabla(request.args[-1])
            links=[]
            if reg.cfg_tip != valNum(id):
                defaults['editable'] = False
                tabla.atr.default = reg.atr
                tabla.valores.default = reg.valores
                tabla.val_def.default = reg.val_def
                current.request.args.remove(request.args[-1])
                current.request.args[-2]='new'
        else:
            links=[]
        grid = SQLFORM_plus(query, links=links, fields=fields, left=left, orderby=orden,field_id=db.mod_cfg_tip_atr.id, **defaults)()
    else:
        grid = SQLFORM_plus(query, links=[], fields=fields, maxtextlength=50,orderby=orden,details=False, editable=False,
                            create=False,field_id=db.mod_cfg_tip_atr.id,
                            deletable=False, csv=False, searchable=False, left=left, title='Atributos')()
        grid['grid'].elements('div.web2py_counter', replace=None)

    return grid

"""    lambda row: A ('', _title='Borrar este registro', cid=request.cid,
                              _href=URL(c='cfg',f='grid_mod_cfg_tip.load',args=['delete','mod_cfg_tip',row[db.mod_cfg_tip.id]],vars=request.vars),
                              _class='btn btn-default btn-secondary glyphicon glyphicon-trash') if  db.mod_cfg_tip(row[db.mod_cfg_tip.id]).cfg==int(request.vars.cfg_id) else ''
                ]
                """

@auth.requires_login()
def grid_cfg_tip_mod():
    idvar = 'cfgtip_id'
    filtra_lista_request_vars(request.vars, idvar)
    #lista=cfgmod_genera_kits(db, idcfgtip= request.vars[idvar])
    request.vars.cfg_id=db.mod_cfg_tip(request.vars[idvar]).cfg
    return grid_cfg_mod()
