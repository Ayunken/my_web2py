# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------
import gluon.contenttype
from plugin_jstree import JsTree
import datetime
from plugin_selectplus import multiTab_widget, SelectTreeWidget
from basic import windows_popup_load
import os
#funciones para llamar a cerrar la ventana de dialogo que selectplus abre por una funcion diferente de la estandar
from plugin_selectplus import selectaddplus_close_dialog, AutocompleteWidgetSelectOrAddOption

if False:
    from gluon import *
    from db import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

#from plugin_sqleditable.editable import SQLEDITABLE
#SQLEDITABLE.init()

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
      """
    response.flash = T("Bienvenido")
    return dict(message=T('Bienvenido a Kit!'))

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)
"""
def testform():
    from formularios import *
    #response.headers['Content-Type'] = 'application/pdf'
    #return genera_formulario_recepcion(db,181292,'18/2456',u'Ramón Ocaña')
    filepath="//server/invifile/PROVEEDORES/000111/inspeccion_pte/181779_alb1234.pdf"
    resp=verifica_formulario_recepcion(filepath)
    raise HTTP(400, BEAUTIFY(resp))

def testbulto():
    campos={'id':204929045,'idembalajeprincipal':5901,'pesoembalaje':15,'idcarga':10227,'numerobulto':36,'pedido':20181054
            ,'fechaalta':'13/04/2018 10:00:00'}
    resp=db.cab_bultos.validate_and_insert(**campos)
    raise HTTP(400, BEAUTIFY(resp))
def recuperanota():
        import time
        id='20181050'
        serie='NE'
        row=db(db.entregas.id==id).select()
        if row:
            filename=id+'.pdf'
            firma = os.path.join(request.folder, 'uploads', 'NE%s.jpg'%id)
            filepath = os.path.join(myconf.get('paths.docs'), serie, filename)
            start = time.time()
            imprime_nota(row,firma,dest=filepath)
            row0=db.entregas0(id)
            resp=row0.update_record(estado=806)
            end = time.time()
            return (end-start)
def test_nota():
    id=20180003
    filepath = os.path.join(request.folder, 'uploads', 'NE%s.jpg'%id)
    #imagen=open(filepath,"r").read()
    row=db(db.entregas.id==id).select()
    if row:
        #destino = os.path.join(myconf.get('paths.docs'), 'NE', str(id))
        return imprime_nota(row,filepath)
    else:
        raise HTTP(400,"No existe mod %s" %id)
"""
def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


def testpdf():
    idproveedor=423
    id='181789'
    albaran='inventado'
    campos={'PROVEEDOR':'FORFLESA','PEDIDO':id,'ALBARAN':albaran, 'BIEN11':'Sí','BIEN12':'Sí','BIEN13':'Sí','paginas':'1'}
    serie='PP'
    filename = '%s_alb%s.pdf'%(id,albaran)
    camino=os.path.join(myconf.get('paths.docsprov') ,'%06d'% idproveedor)
    camino=os.path.join(camino,'inspeccion_pte')
    filepath = os.path.join(camino,filename)
    response.view='generic.%s' % request.extension
    from formularios import genera_formulario_recepcion
    resp= genera_formulario_recepcion(db,campos,filepath)
    return locals()

def test_mail():
    bases = ['inverca.es']
    prefixes = ['smtp.']
    ports = [':587'] #[':25', ':465', ':993', ':587', '']
    sender = 'someone@yourdomain.com'
    login = 'inverca:inverwin1980'
    send_test_to = 'juliodelbarrio@gmail.com'
    count = 0
    mail.settings.tls = True #Here so you can set to False if things fail?
    for base in bases:
        for prefix in prefixes:
            for port in ports:
                server = '{0}{1}{2}'.format(prefix, base, port)
                msg = 'server: {0} login: {1}'.format(server, login)
                # So you can correlate with error codes. Note some servers don't like print!
                print (msg)
                mail.settings.server = server
                mail.settings.sender = sender
                mail.settings.login = login
                mail.send(to=[send_test_to],
                    subject='hello',
                    reply_to='jbs@inverca.es',
                    message=msg
                    )
                count += 1
    return dict(message="tried {0} combinations".format(count))
def correo():
    response.view='grid.%s' % request.extension
    form=SQLFORM.factory(Field('name'),Field('email'),Field('asunto'),Field('message'))
    if form.process().accepted:
        session.name = form.vars.name
        session.email = form.vars.email
        session.subject = form.vars.subject
        session.message = form.vars.message
        if mail:
            mail.settings.tls = True
            mail.settings.ssl = True
            if mail.send(to=['jbs@inverca.es'],
                subject='asunto',
                message= "Hello this is an"):
                response.flash = 'email sent sucessfully.'
            else:
                response.flash = 'fail to send email sorry! %s'%mail.settings.server
        else:
            response.flash = 'Unable to send the email : email parameters not defined'
    return  dict(grid=form)


def grid_mod_atr_old():
    query = db.mod_atr
    if  'mod_grp_atr_id' in request.vars:
        if  isinstance(request.vars.mod_grp_atr_id, (list, tuple)):
            request.vars.mod_grp_atr_id=request.vars.mod_grp_atr_id[0]
        raiz=db.mod_grp_atr(request.vars.mod_grp_atr_id)
        if raiz: #si no tiene padre, no lo filtro, es el tipo raiz y con el muestro todos los modulos
            if raiz.parent:
                query = db(db.mod_atr.grp_atr==request.vars.mod_grp_atr_id)
                db.mod_atr.grp_atr.default=request.vars.mod_grp_atr_id
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    response.view='grid.%s' % request.extension
    if not ('new' in request.args or 'edit' in request.args):
        db.mod_atr.val_def.writable=db.mod_atr.val_def.readable=False
    db.mod_atr.rango.readable=db.mod_atr.val_def_formula.readable=False
    grid= SQLFORM_plus(query,fields=report_fields_list(db)['mod_atr'],links=[],title=db.mod_atr._plural,format='L',orderby=db.mod_atr.name,**defaults)
    if len(request.args)>1 and not 'new' in request.args:
         return view_mod_atr_tabs0(grid.grid,botones_back(request,f=request.function))
    else:
        return grid()




def view_mod_tabs0(form,botones):
    reg=db.mod(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], [T('Componentes'),dict(f='grid_mod_cmp.load', vars=dict(mod_id=reg.id),user_signature=True)],[T('Atributos'),dict(f='grid_mod_mod_atr.load',vars=dict(mod_id=reg.id),user_signature=True)],[T('Piezas'),dict(f='grid_mod_pie.load',vars=dict(mod_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod._singular,tablename='mod')

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

def grid_mod_tipo():
    filtra_lista_request_vars(request.vars, 'mod_tipo_id')
    db.mod_tipos.id.readable=False
    form = SQLFORM(db.mod_tipos, record=request.vars.mod_tipo_id,fields=['abreviatura'],_name='form_mod_tipos')
    if form.process().accepted:
        response.flash = 'abreviatura cambiada'
    db.mod.tipo.default=request.vars.mod_tipo_id
    grid=grid_mod()
    if len(request.args) > 1 and not 'new' in request.args:
        return grid
    else:
        response.view='default/grid_mod_tipo.load'
        return dict( formulario=form,**grid)

def grid_mod():
    query = db.mod
    create=True
    left = []
    fields = [db.mod.name, db.mod.tipo]
    #if len(request.args)>1 :
    #    redirect(URL(r=request,f='view_mod_tabs',args=request.args,vars=request.vars,user_signature=True))
    if filtra_lista_request_vars(request.vars, 'mod_tipo_id'):
        raiz=db.mod_tipos[request.vars.mod_tipo_id]
        query=mptt.descendants_from_node(request.vars.mod_tipo_id,include_self=True)(db.mod.tipo==db.mod_tipos.id)

    elif filtra_lista_request_vars(request.vars, 'mod_atr_id'):
        query=db((db.mod_mod_atr.atr==request.vars.mod_atr_id)  &  (db.mod.id==db.mod_mod_atr.mod))
        #left=[db.mod.on((db.mod_mod_atr.mod==db.mod.id))]
        create=False
        db.mod_mod_atr.atr.default=request.vars.mod_atr_id
    else:
        fields = [db.mod.id]+ fields + [db.mod.um]
    defaults=GRAL().grid_pdf_defaults.copy() if request.extension=='pdf' else GRAL().grid_defaults.copy()
    defaults['orderby']=[db.mod.tipo]
    response.view='grid.%s' % request.extension
    links=[lambda row: A('',_title='Componentes en ventana',_onclick='openform_modcmp(%(id)s,"%(name)s");'%row,_class='btn btn-default btn-secondary glyphicon glyphicon-list')]
    grid=SQLFORM_plus(query,links=links,field_id =db.mod.id,create=create,left=left,fields=fields,title=db.mod._plural,**defaults)
    gridp=grid()
    gridp['grid'].components.extend([windows_popup_load('modcmp','grid_mod_cmp0','mod_id')])
    
    if len(request.args)>1 and not 'new' in request.args:
        return view_mod_tabs0(grid.grid,botones_back(request,f=request.function))
    else:
    #si estamos en una ventana, y se ha dado de alta, pasamos a la vista edit
        return gridp

def grid_mod_cfg_mod():
    filtra_lista_request_vars(request.vars, 'cfg_id')
    query=db.mod_cfg_mod.cfg==request.vars.cfg_id
    jsadd=None
    if 'mod_tipo_id' in request.vars:
        query= (query) & (db.mod_cfg_mod.tipo==request.vars.mod_tipo_id)
        db.mod_cfg_mod.tipo.default =request.vars.mod_tipo_id
        db.mod_cfg_mod.tipo.writable=False
        row=db((db.mod_cfl_tip.cfl==db.mod_cfg.cfl_base) & (db.mod_cfg.id==request.vars.cfg_id) & (db.mod_cfl_tip.mod_tipo== request.vars.mod_tipo_id)).select(db.mod_cfl_tip.formula)
        if row:
            db.mod_cfg_mod.formula.default = row[0].formula
        filtro=db.mod_tipos.id==request.vars.mod_tipo_id
        parent=db.mod_tipos[db.mod_cfg_mod.tipo.default].parent
        db.mod_cfg_mod.mod.requires=IS_IN_DB(db((db.mod.tipo==db.mod_cfg_mod.tipo.default) | (db.mod.tipo==parent)), 'mod.id', '%(name)s', orderby='name',zero=T("Selecciona módulo"))
        db.mod_cfg_mod.mod.widget=SelectOrAddOption( db.mod, select_id="modcfgmod",controller='default',function='view_mod_tabs')
        """
        * así sería seleccion del modulo  en contexto de jerarquia de modulos, pero como solo va a listar un nodo y como mucho su pader, mejor en un select normal
          db.mod_cfg_mod.mod.widget = SelectTreeWidget(request, mptt, db.mod.name, id_field=db.mod.id, db=db,
                                                     keyword="modcfgmod", field_reference_tree=db.mod.tipo,
                                                     filter=filtro,
                                                     filterdata={"mod_tipo_id": request.vars.mod_tipo_id,"cfg_id": request.vars.cfg_id})
        """
        if 'refreshtree' in current.session:
            jsadd = '(function($) {F%s_refresh(%s,%s);})(jQuery);' % ('jstree_cfgtipmod', db.mod_tipos(request.vars.mod_tipo_id).parent, request.vars.mod_tipo_id)
            jsadd = SCRIPT(jsadd, _type="text/javascript")
            del current.session.refreshtree
        if ('mod' in request.vars and ('new' in request.args or 'edit' in request.args)) or ('delete' in request.args):
            current.session['refreshtree'] = 1

    query=db(query)
    left=[]
    #left=[db.mod_tipos.on(db.mod_tipos.id==db.mod_cfg_mod.tipo)]
    fields=[db.mod_cfg_mod.tipo, db.mod_cfg_mod.mod,db.mod_cfg_mod.formula]
    db.mod_cfg_mod.cfg.default=request.vars.cfg_id
    db.mod_cfg_mod.cfg.readable=db.mod_cfg_mod.cfg.writable=False
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid= SQLFORM_plus(query,links=[],fields=fields,left=left,title='Componentes',**defaults)
    grid = grid()
    cambiado=False
    if jsadd:
        grid['grid'].components.extend([jsadd])
    """ ESTO SIRVE PARA RECARGAR LA PAGINA ENTERA DESDE UN AJAX COMPONENT O LOAD
    redirect(request.env.http_web2py_component_location, client_side=True)
    """
    return grid

def grid_mod_cfg_tipos():
    filtra_lista_request_vars(request.vars, 'cfg_id')
    divmod='divmodcfg'
    url=URL(f='grid_mod_cfg_mod.load',vars=dict(mod_tipo_id='node_id',cfg_id=request.vars.cfg_id),user_signature=True)
    cfl=db.mod_cfg[request.vars.cfg_id].cfl_base
    filtro=((db.mod_cfl_tip.cfl==cfl) & (db.mod_cfl_tip.mod_tipo==db.mod_tipos.id))
    datosfiltro={"cfg_id": request.vars.cfg_id}
    #jstree = JsTree(mptt, renderstyle=True,search=True,selectcomponent=[url,divmod],keyword='jstree_cfgtipmod',filter=filtro,filterdata=datosfiltro,edit_option=False)
    jstree=JsTree_cfgmod(mptt, request.vars.cfg_id, renderstyle=True, search=True, selectcomponent=[url, divmod], keyword='jstree_cfgtipmod',
       filter=filtro, filterdata=datosfiltro, edit_option=False)
    #jstree=JsTree2(mptt, selectcomponent=[url,divmod],keyword='jstree_cfgtipmod',filter=filtro,filterdata=datosfiltro)
    ### populate records ###########################################################
    if not mptt.roots().count():
        _root1 = mptt.insert_node(None, name='raiz', node_type='root')
    title=db.mod_tipos._plural
    query=db.mod_tipos
    response.view='tree_grid.%s' % request.extension
    grid=DIV(_id=divmod,_class='col-md-8')
    return dict(title=title,arbol=DIV(jstree(),_class='col-md-4'),grid=grid)

def grid_mod_cfg_atr():
    filtra_lista_request_vars(request.vars, 'cfg_id')
    query=db(db.mod_cfg_atr.cfg==request.vars.cfg_id)
    db.mod_cfg_atr.cfg.default=request.vars.cfg_id
    db.mod_cfg_atr.cfg.writable=False
    left=[db.mod_atr.on((db.mod_cfg_atr.atr==db.mod_atr.id))]
    fields=[db.mod_atr.name,db.mod_atr.grp_atr,db.mod_cfg_atr.rango,db.mod_cfg_atr.val_def,db.mod_cfg_atr.lock]
    #grid=SQLFORM.grid(query,links=[],fields=fields,left=left)
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid=SQLFORM_plus(query,links=[],fields=fields,left=left,field_id=db.mod_cfg_atr.id,title='Atributos',**defaults)
    return grid()


def grid_mod_cfl_atr():
    filtra_lista_request_vars(request.vars, 'cfl_id')
    query=db(db.mod_cfl_atr.cfl==request.vars.cfl_id)
    db.mod_cfl_atr.cfl.default=request.vars.cfl_id
    db.mod_cfl_atr.cfl.writable=False
    left=[db.mod_atr.on((db.mod_cfl_atr.atr==db.mod_atr.id))]
    fields=[db.mod_atr.name,db.mod_atr.grp_atr,db.mod_cfl_atr.rango,db.mod_cfl_atr.val_def]
    #grid=SQLFORM.grid(query,links=[],fields=fields,left=left)
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid=SQLFORM_plus(query,links=[],fields=fields,left=left,field_id=db.mod_cfl_atr.id,title='Atributos',**defaults)
    return grid()


def grid_mod_cfl_tip():
    filtra_lista_request_vars(request.vars,'cfl_id')
    query=db(db.mod_cfl_tip.cfl==request.vars.cfl_id)
    #left=[db.productos.on(db.productos.id==db.mod_cmp.cmp_pie),db.mod.on(db.mod.id==db.mod_cmp.cmp_mod)]
    left=[db.mod_tipos.on(db.mod_tipos.id==db.mod_cfl_tip.mod_tipo)]
    fields=[db.mod_tipos.name,db.mod_cfl_tip.min_mods, db.mod_cfl_tip.formula]
    db.mod_cfl_tip.cfl.default=request.vars.cfl_id
    db.mod_cfl_tip.cfl.readable=db.mod_cfl_tip.cfl.writable=False
    response.view='grid.%s' % request.extension
    defaults=GRAL.grid_pdf_defaults if request.extension=='pdf' else GRAL.grid_defaults
    grid= SQLFORM_plus(query,links=[],fields=fields,left=left,field_id=db.mod_cfl_tip.id,title=db.mod_cfl_tip._plural,**defaults)
    return grid()

def view_cfg_tabs0(form,botones):
    reg=db.mod_cfg(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], \
         [T('Tipos Modulos'), dict(f='grid_mod_cfg_tipos.load', vars=dict(cfg_id=reg.id), user_signature=True)], \
         [T('Componentes'),dict(f='grid_mod_cfg_mod.load', vars=dict(cfg_id=reg.id),user_signature=True)], \
         [T('Atributos'),dict(f='grid_mod_cfg_atr.load',vars=dict(cfg_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs,tab_id="tabcfg")
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_cfg._singular,tablename='mod_cfg')

def view_cfl_tabs0(form,botones):
    reg=db.mod_cfl(request.args[-1])
    tabs=[T('Datos'),dict(content=form)], \
         [T('Atributos Base'),dict(f='grid_mod_cfl_atr.load',vars=dict(cfl_id=reg.id),user_signature=True)], \
         [T('Tipo de Módulo'),dict(f='grid_mod_cfl_tip.load',vars=dict(cfl_id=reg.id),user_signature=True)]
    tabs=multiTab_widget(tabs)
    response.view='tabs.%s' % request.extension
    return dict(ficha=reg,botones=botones,tabs=tabs,title=db.mod_cfl._singular,tablename='mod_cfl')

def view_cfl_tabs():
    tabla=db.mod_cfl
    back_f = 'grid_mod'
    formname = 'form_%s' % tabla._tablename
    if len(request.args) < 4:  # esto indicaría que no está en una ventana de un select_add/edit
        botones = botones_back(request, f=back_f)
    else:
        botones = ''
    if 'new' in request.args:
        form = SQLFORM(tabla, _name=formname)  # add
        response.view = 'grid.%s' % request.extension
        if len(request.args) == 3:
            botones = ''
            selectaddplus_close_dialog(response, request, form, db)
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form, botones=botones, title='Nuevo %s' % tabla._singular)
    else:
        if len(request.args) > 1:
            form = SQLFORM(tabla, request.args[-1], _name=formname)  # edit/update/change
            if len(request.args) == 4:  # esto es que se está en una ventana de dialogo uI
                selectaddplus_close_dialog(response, request, form, db)
            elif form.process(formname=formname).accepted:
                redirect(URL(back_f))
            return view_mod_tabs0(form, botones)
        else:
            session.flash=T('%s no existe') % (tabla._singular)
            redirect(URL(back_f))

def view_cfg_tabs():
    tabla=db.mod_cfg
    back_f = 'grid_mod'
    formname = 'form_%s' % tabla._tablename
    if len(request.args) < 4:  # esto indicaría que no está en una ventana de un select_add/edit
        botones = botones_back(request, f=back_f)
    else:
        botones = ''
    if 'new' in request.args:
        form = SQLFORM(tabla, _name=formname)  # add
        response.view = 'grid.%s' % request.extension
        if len(request.args) == 3:
            botones = ''
            selectaddplus_close_dialog(response, request, form, db)
        elif form.process(formname=formname).accepted:
            redirect(URL(back_f))
        return dict(grid=form, botones=botones, title='Nuevo %s' % tabla._singular)
    else:
        #db.mod_cfg.cfg_base.writable=False
        if len(request.args) > 1:
            form = SQLFORM(tabla, request.args[-1], _name=formname)  # edit/update/change
            if len(request.args) == 4:  # esto es que se está en una ventana de dialogo uI
                selectaddplus_close_dialog(response, request, form, db)
            elif form.process(formname=formname).accepted:
                redirect(URL(back_f))
            return view_mod_tabs0(form, botones)
        else:
            session.flash=T('%s no existe') % (tabla._singular)
            redirect(URL(back_f))

def grid_cfg():
    tabla=db.mod_cfg
    query = db.mod_cfg
    create=True
    if filtra_lista_request_vars(request.vars,'mod_id'):
        query=db((db.mod_cfg_mod.mod==request.vars.mod_id)  &  (tabla.id==db.mod_cfg.cfg))

    if filtra_lista_request_vars(request.vars, 'mod_atr_id'):
        query=db((db.mod_cfg_atr.atr==request.vars.mod_atr_id)  &   (tabla.id==db.mod_cfg_atr.cfg))
        left=[]
        create=False
        db.mod_cfg_atr.atr.default=request.vars.mod_atr_id
    else: left=[]
    fields=[tabla.id,tabla.name,tabla.cfl_base]
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    response.view = 'grid.%s' % request.extension
    grid = SQLFORM_plus(query, links=[], field_id=db.mod_cfg.id, create=create, left=left, fields=fields,
                        title=tabla._plural, **defaults)
    if len(request.args) > 1 and not 'new' in request.args:
        return view_cfg_tabs0(grid.grid, botones_back(request, f=request.function))
    else:
        return grid()

def grid_cfl():
    tabla=db.mod_cfl
    query = db.mod_cfl
    create=True
    left=[]
    fields=[tabla.id,tabla.name]
    defaults = GRAL.grid_pdf_defaults if request.extension == 'pdf' else GRAL.grid_defaults
    response.view = 'grid.%s' % request.extension
    grid = SQLFORM_plus(query, links=[], field_id=db.mod_cfl.id, create=create, left=left, fields=fields,
                        title=tabla._plural, **defaults)
    if len(request.args) > 1 and not 'new' in request.args:
        return view_cfl_tabs0(grid.grid, botones_back(request, f=request.function))
    else:
        return grid()

def mod_tipos():
    ### inject the mptt tree model to the jstree plugin ###
    divmod='divmodulos'
    url=URL(f='grid_mod_tipo.load',vars=dict(mod_tipo_id='node_id'),user_signature=True)
    jstree = JsTree(tree_model=mptt, renderstyle=True, version=3, search=True,selectcomponent=[url,divmod],
                    keyword='jstree_tipmod',count_descendants=True)
    ### populate records ###########################################################
    if not mptt.roots().count():
        _root1 = mptt.insert_node(None, name='/', node_type='root')
    """
        _child1 = mptt.insert_node(_root1, name='child1')
        mptt.insert_node(_root1, name='child2')
        mptt.insert_node(_child1, name='grandchild1')
        mptt.insert_node(None, name='root2', node_type='root')
    """
    title=db.mod_tipos._plural
    query=db.mod_tipos
    grid=DIV(_id=divmod,_class='col-md-8')
    j=jstree()
    return dict(title=title,arbol=DIV(j,_class='col-md-4'),grid=grid)



def grid_mod_atr():
    query = db.mod_atr
    if filtra_lista_request_vars ( request.vars,'mod_grp_atr_id'):
        raiz = db.mod_grp_atr(request.vars.mod_grp_atr_id)
        if raiz:  # si no tiene padre, no lo filtro, es el tipo raiz y con el muestro todos los modulos
            if raiz.parent:
                query = db(db.mod_atr.grp_atr == request.vars.mod_grp_atr_id)
                db.mod_atr.grp_atr.default = request.vars.mod_grp_atr_id
    filtra_lista_request_vars(request.vars, 'order')
    response.view='grid.%s' % request.extension

    if not ('new' in request.args or 'edit' in request.args):
        db.mod_atr.val_def.writable=db.mod_atr.val_def.readable=False
    db.mod_atr.rango.readable=db.mod_atr.val_def_formula.readable=False
    defaults = GRAL.grid_pdf_defaults.copy() if request.extension == 'pdf' else GRAL.grid_defaults.copy()

    if len(request.post_vars) > 0:
        for key, value in request.post_vars.iteritems():
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
    grid = SQLFORM_plus(query, fields=fields, links=[], title=db.mod_atr._plural, format='L', **defaults)
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
        return gridp
