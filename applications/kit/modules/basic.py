#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
import datetime
T=current.T
import sys
#FUNCIONES BASICAS HORIZONTALES, COMUNES A CUALQUIER APLICACION
def miencode(t):
    return t.decode('UTF-8').encode('windows-1252')

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def valNum(var):
    try: return float(var)
    except: return 0

def valStr(var):
    return '' if var is None else var

def valNumOrStr(var):
    try:
        f=float(var)
        i = int(f)
        if i!=f:
            return f
        else:
            return i
    except:
        return var
# funcion recursiva que extrae en ul/li todo el árbol
def tree_carga_nodo(db,tabla,parent):
    rows=db(tabla.parent==parent)
    if  rows.count()>0:
        return UL(*[LI(x.name,tree_carga_nodo(db,tabla,x.id),_id=str(x.id)) for x in rows.select()])
    else:
        return ''
def tree_have_children(db,tabla,id):
    if db(tabla.parent==id).count()>0:
        return True
    else:
        return False

#funcion que extrae la lista de un nodo y por cada uno solo dice si tiene o no hijos
def tree_get_node(db,tabla,parent):
    rows=db(tabla.parent==parent)
    if  rows.count()>0:
        childs=[]
        for x in rows.select():
            childs.append ({"text": x.name,"children": tree_have_children(db,tabla,x.id), "id": str(x.id)})
        if parent==None:
            childs=dict(id=-1,text='Tipos',children=childs)
        return childs
    else:
        return dict(id=-1,text='Tipos',children=False)


"""
def options_widget(field,value,**kwargs):
    # Use web2py's intelligence to set up the right HTML for the select field
    # the widgets knows about the database model
    w = SQLFORM.widgets.options.widget
    xml = w(field,value,**kwargs)
    return xml
"""
# there is no need to be so verbose. This works as well.
def options_widget(field,value,**kwargs):
    from gluon.sqlhtml import OptionsWidget
    return OptionsWidget.widget(field, value,**kwargs)
def string_widget(field,value,**kwargs):
    return SQLFORM.widgets.string.widget(field,value,**kwargs)
def boolean_widget(field,value,**kwargs):
#be careful using this; checkboxes on forms are tricky. see notes below.
    return SQLFORM.widgets.boolean.widget(field,value,**kwargs)


class Compute_lazy(object):
    """
        -Se asigna como widget a un campo de tabla para calcular su valor mediante una lambda en tiempo de formulario pudiendo usar los
        valores de los campo del formulario
        -Ejecuta la funcion lambda pasada cuando uno de los campos de la lista triggers es modificado. usa Ajax
        -La funcion lambda recibe 3 parametros: valor actual campo, nombre campo disparador, DICT registro
    """
    def __init__(self,funcion,triggers,keyword='_compute_lazy_%(fieldname)s',user_signature=False,hmac_key=None,visible=True,widget_custom=None):
        self.funcion,self.triggers,self.keyword,self.user_signature,self.hmac_key,self.visible= funcion,triggers,keyword,user_signature,hmac_key,visible
        if not isinstance(triggers,(list,tuple)):
            self.triggers=[triggers]
        self._triggers=(', '.join(['#%s_%s' %(i._tablename,i.name) for i in self.triggers]))
        self._widget=widget_custom
    def _compute(self, trigger, field, value, vars):
        if callable(self.funcion):
            return self.funcion(value,trigger,vars)
        else:
            return self.funcion % dict(value=value,**vars)

    def _pre_process(self, field):
        self._keyword = self.keyword % dict(fieldname=field.name)
        self._el_id = '%s_%s' % (field._tablename, field.name)
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            requires = requires.other
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], 'options'):
                self._require = requires[0]
            else:
                self._require= None
        else:
            self._require = None

    def process_now(self, field,value):
        if not hasattr(self, '_keyword'):
            self._pre_process(field)

        if self._keyword in current.request.vars:
            if self.user_signature:
                if not URL.verify(current.request, user_signature=self.user_signature, hmac_key=self.hmac_key):
                    raise HTTP(400)

            trigger = current.request.vars[self._keyword]
            vars={}
            if trigger:
                #aqui saco todas la variables con prefijo igual al de la tabla
                prefix='%s_'%field._tablename
                for k in current.request.vars:
                    if k.startswith(prefix):
                        vars[k.replace(prefix,'')]=current.request.vars[k]
            raise HTTP(200, self._compute(trigger,field,value,vars))
        return self

    def __call__(self, field, value, **attributes):
        request = current.request
        if hasattr(request, 'application'):
            self.url = URL(r=request, args=request.args,
                           user_signature=self.user_signature, hmac_key=self.hmac_key)
            self.process_now(field,value)
        else:
            self.url = request

        #añadir aqui otros widges posibles como check
        if self._widget:
            wd=self._widget(field, value,**attributes)
        elif self._require:
            wd=options_widget(field, value,**attributes)
        else:
            wd=string_widget(field, value,**attributes)
        if not self._widget:
            wd['_class'] = 'generic-widget form-control'
        self._el_id = '%s_%s' % (field._tablename, field.name)
        if self.visible==False:
            jsocultar='$("#%s__row").hide();' % self._el_id
        else:
            jsocultar=''
        js=SCRIPT("""
           $(function() {
           $("%(triggers)s").change(function(e){
           var query = {};
           var val=$( this ).val();
           query["%(keyword)s"] = this.id;
           query[this.id]=val;
           $.ajax({type: "POST", url: "%(url)s", data: query,
            success: function(value) {$("#%(el_id)s").val(value);$("#%(el_id)s").change();
            }})}); });
%(jsadd)s

""" % dict(triggers=self._triggers,url=self.url,el_id=self._el_id,keyword=self._keyword,jsadd=jsocultar))
        #wd.components.append(js)
        return DIV(wd,js)


class Input_compute_in_form(object):  #and even EDIT
    """
        Se asigna como widget a nu campo string
       añade codigo javascript que calcula el valor del campo  mediante la funcion javascript pasada en 'function'
       Util para establecer un campo en funcion de otro.
       e.g.: function='$("[name=\'name\']").val().substring(0,20)'  # copia el campo 'name' y lo recorta a 20 caracteres y lo establece al campo destino
       El parametro opcional set_if_null habilita que se calcule siempre o solo cuando esté en blanco el campo destino
    """
    def __init__(self,  function,set_if_null=True ):
        self._funcion=function
        self._set_if_null=set_if_null
    def __call__(self,field,value,**attributes):
        from gluon.sqlhtml import StringWidget
        default = dict(
            _type = 'text',
            value = (not value is None and str(value)) or '',
            )
        attr=StringWidget._attributes(field, default, **attributes)
        attr['_class'] = 'form-control string'
        wrap=DIV()
        if self._set_if_null:
            condicion='$(this).val().length == 0'
        else:
            condicion='true'
        wrap.components.extend(TAG[''](INPUT(**attr),
                     SCRIPT('$("[name=\'%s\']").focusin(function(e) {if (%s) $(this).val(%s);});' %  (attr['_name'], condicion, self._funcion))))
        return wrap



def grid_footer_align(fields,values):
    footer=[]
    for  f in fields:
        namefield=f.__str__()
        if values.has_key(namefield):
            if (f.type=='decimal(9,2)') :
                footer.append(TH(GRAL().represent_currency(values[namefield]),_align='right'))
            elif (f.type.startswith('decimal') or f.type=='integer'):
                footer.append(TH(values[namefield], _align='right'))
        else:
            footer.append(TH(' '))
    return footer


def grid_footer_add_totals(db,grid,query,fields,left=None,offset=0):
    '''
    Agrega Totales segun la lista de campos de fields
    Totaliza todos los campos que se ha añadido el atributo ..field._extra={'total':True}
    '''
    from pydal.objects import Query,Table
    request=current.request
    s=[]
    pies={}
    for f in fields:
        if hasattr(f,'_extra'):
            if f._extra['total']:
                if f.name.endswith('*sum'):
                    s.append(db[f.tablename][f.name.split('*')[0]].sum())
                elif f.name.endswith('*count'):
                    s.append(db[f.tablename][f.name.split('*')[0]].count())
                else:
                    s.append(f.sum())
    if s:
        #hay que distinguir si viene un query o un set porque no está claro
        if isinstance(query,Query):
            query=db(query)
        elif isinstance(query,Table):
            query=db(query.id>0)
        #hasta aqui la query es ya un Set
        if  'keywords'  in request.vars:
            if len(request.vars.keywords)>0:
                query=query(SQLFORM.build_query(fields,request.vars.keywords))
        row=query.select(*s, left=left).first()
        for f in fields:
            if hasattr(f,'_extra'):
                if f._extra['total']:
                    if f.name.endswith('*sum'):
                        pies[f.__str__()]=row[db[f.tablename][f.name.split('*')[0]].sum()]
                        if f.__str__().startswith('AVG('):
                            pies[f.__str__()]=None #row[db[f.tablename][f.name.split('*')[0]].count()]
                        #ya es un sumatorio, no voy a sumar la suma de sumas
                    elif f.name.endswith('*count'):
                        pies[f.__str__()] = row[db[f.tablename][f.name.split('*')[0]].count()]
                    else:
                        pies[f.__str__()]=row[f.sum()]
                        #pies[f.__str__()]=row[f._extra['field_summed'].sum()]
    if pies and grid.element('.web2py_htmltable tbody'):
        grid.element('.web2py_htmltable tbody').append((TR(grid_footer_align(fields,pies,offset=offset) ,_id='tot_gral')))
    pass
""" widgets para el sqlform sea editable in line """


def query_humanize(str,fieldname,table,is_string=True):
    """
    busca en 'str' un asignacion del campo 'fieldname'
    para cambiarlo por el format de la 'table'
    y con el is_string = True tiene en cuenta que sea un cadena
    """
    sep='"' if is_string else ' '
    strout=str
    fieldname0=fieldname+"="+sep
    i=str.find(fieldname0)
    if i>-1:
        i=i+len(fieldname0)
        f=str.find(sep,i+1)
        if f==-1: f=len(str)
        id=str[i:f]
        row=table[id]
        if row:
            name=table._format(table[id])
            strout= str[:i]+name.flatten()+str[f:]
    return strout


def grid_create_sumfields(oper='sum',fields='',label=None, length=None, total=False):
    """
    Crea una lista de campos sumatorios para añadir a la lista de campos
    de un query y poder usarlos para sumar un grid con groupby
    """
    res=[]
    for f in fields:
        count={'count':f.count(),'sum':f.sum(), 'avg':f.avg(),'min':f.min(),'max':f.max()}[oper]
        count.tablename = f.tablename
        count.name=f.name + '*'+oper
        count.readable = True
        count.type=f.type #'decimal(9,2)'
        #count.label=DIV(f.label, _style='text-align: right;') #ya le arreamos justificar a la derecha para la etiqueta
        count.label=label or f.label
        count.length=length or 20
        count.represent=f.represent
        count.listable=True
        count.formatter=f.formatter
        count.table = f.table
        if total:
            count._extra={'total':True} #,'field_summed':f} #esto es para grid_footer_add_totalesm así sabe el campo sumado
        res.append(count)
    return res

def grid_headers_align(fields):
    headers={}
    for  f in fields:
        namefield=f.__str__()
        label=f.label
        if namefield.startswith('AVG('): label=T(namefield)
        #if f.type.startswith('decimal') or f.type=='integer' :
            #headers[namefield]=DIV(label, _style='text-align: right;')
            #raise HTTP(404,f.label)
    return headers

def PDFtable(table,format='L',title='Title',subtitle=''):
    '''
    devuelve un PDF de la tabla pasada (normalment procedente de un grid)
    '''
    response=current.response
    request=current.request
    response.title = title
    auth=current.session.auth
    if request.extension == "pdf":
        from gluon.contrib.fpdf import FPDF, HTMLMixin
        # define our FPDF class (move to modules if it is reused frequently)
        class MyFPDF(FPDF, HTMLMixin):
            def header(self):
                y=self.get_y()
                #Esto para hacer codigos de barras o cualquier otro tipo de letra ttf
                #dejar el archivo en /gluon/contrib/fpdf/font
                #self.add_font('BC39', '', '3OF9_NEW.TTF', uni=True)
                #self.set_font('BC39', '', 15)

                #Titulo en medio
                self.set_font('Arial', 'B', 15)
                self.cell(0, 14,response.title.decode('UTF-8').encode('windows-1252'), 1, 0, 'C')
                #Comañia a la izquierda
                self.set_y(y)
                self.set_font('Arial', 'B', 8)
                if auth.user:
                    if 'company' in auth.user:
                        header_left=auth.user.company if auth.user.company else auth.user.username
                    else: header_left=GRAL.labelcompany
                else: header_left=''
                self.cell(0, 10, header_left, 0, 0, 'L')
                #Paginas a la rederecha
                self.set_font('Arial', 'I', 8)
                txt = T('Page %s of %s') % (self.page_no(), self.alias_nb_pages())
                self.cell(0, 10, txt.decode('UTF-8').encode('windows-1252'), 0, 0, 'R')

                self.ln(8)
                self.set_font('Arial', '', 8)
                self.cell(0, 8, subtitle.decode('UTF-8').encode('windows-1252'), 0, 0, 'L')
                self.ln(10)

            def footer(self):
                #self.set_y(-15)
                #self.set_font('Arial', 'I', 8)
                #txt = T('Page %s of %s') % (self.page_no(), self.alias_nb_pages())
                #self.cell(0, 10, txt, 0, 0, 'C')
                pass
            def set_align_cells_from_divs(self,table):
                ''' pasa el atributo align de divs incluidos en celdas a la etiqueta td o th '''
                for tr in table.elements('tr'):
                    for td in tr.elements('td,th'):
                        if td.element('div',_style='text-align: right;'):
                            td['_align']='right'
                        else:
                            td['_align']='left'

        pdf = MyFPDF(format)
        # first page:
        pdf.add_page()
        if table:
            pdf.set_align_cells_from_divs(table)
            pdf.set_y(12)
            #estas htmlentities provocan que salte una columna, básicamente cualquier caracter & lo hace
            table=str(table).replace('&amp;','_')
            table=str(table).replace('&#x27;',"'")
            pdf.write_html('<font size="8">' + table.decode('UTF-8').encode('windows-1252')+ '</font>')
        response.headers['Content-Type'] = 'application/pdf'
        return pdf.output(dest='S')
    else:
        # normal html view:
        response.view='default/test.html'
        return dict(table=table)


class SQLFORM_plus():
    '''
    Añade al grid boton PDF en exports
    Retorna salida a pdf o vista grid
    title=Titulo del listado ya traducido
    Como subtitulo ir á keywords
    anchor=lista de anchos de cada columna para el PDF
    format: P= vertical L=apaisado (formato de página del PDF
    El subtitulo lo montará en base a las keywords del grid de vars.keywords
    '''
    def grid(self):
        return self.grid
    def _largo_campo(self,field):
        if field.type.startswith('decimal'):
            return 12
        elif field.type.startswith('date'):
            return 15
        elif field.length:
            if field.length<5:
                return 5
            else:
                return field.length if field.length<30 else 30
    def _establece_ancho_columnas(self,anchor,fields,table):
        ths= table.elements('th')
        if anchor:
            for i in range(0,len(anchor)):
                ths[i]['_width']=anchor[i]
        elif fields:
            total=0
            res=[]
            l=0
            for f in fields:
                total+=self._largo_campo(f)
            for i in range(0,len(fields)):
                l=self._largo_campo(fields[i])*100/total
                if l<1 : l=1
                ths[i]['_width']='%3d%%' % l
                res.append(ths[i]['_width'])
        return None

    def __init__(self,query,**args):
        self.anchor=None
        self.title=None
        self.fields=None
        self.db=query._db
        self.rowtotals = None
        self.format='L'
        self.response=current.response
        self.request=current.request
        self.selectpaginate=True
        self.formcopy=False
        self.formupd=False
        self._all_records_selector_enabled = False
        self.formadd=False
        if 'rowtotals' in args:
            self.rowtotals = args['rowtotals']
            del args['rowtotals']
        if 'fields' in args:
            self.fields=args['fields']
        else:
            self.fields=[[f]  for f in query.fields]
        if 'title' in args:
            self.title=args['title']
            del args['title']
        if self.request.extension == 'pdf':
            if 'links' in args:
                del args['links']
            args['create'] = False
            args['deletable'] = False
            args['editable'] = False
            args['sortable'] = False
        if 'anchor' in args:
            self.anchor=args['anchor']
            del args['anchor']
        if 'format' in args:
            self.format=args['format']
            del args['format']
        if 'selectpaginate' in args:
            self.selectpaginate=args['selectpaginate']
            del args['selectpaginate']
        if self.selectpaginate:
            if 'paginate' in self.request.vars:
                filtra_lista_request_vars(self.request.vars, 'paginate')
                args['paginate'] = int(self.request.vars.paginate) if is_number(self.request.vars.paginate) else None
        if  not ('formname' in args):
            import uuid
            args['formname']='%s'% (self.request.function) #,str(uuid.uuid4())[:8])
        if 'formadd' in args:
            self.formadd=args['formadd']
            del args['formadd']
        if 'formcopy' in args:
            self.formcopy=args['formcopy']
            if self.formcopy:
                self.formcopy['copy']=    self.formcopy.get('copy',True)
                self.formcopy['delete']=    self.formcopy.get('delete',True)
                self.formcopy['fields']=    self.formcopy.get('fields',[])
                if not self.formcopy['fields']:
                    self.formcopy['fields']=[Field('copy_name', 'string',label=T('Patrón nueva descripcion'),default=T("'Copia de '+%s"),comment=T("%s se sustituye en destino por la descripción del reg origen. Escribir cadenas entre comillas simples. Para unir cadenas usar símbolo +"),requires=IS_NOT_EMPTY())]
                self.formcopy['callback']=self.formcopy.get('callback',self._copiador_callback)
                args['selectable']=self._callbackbatch
            del args['formcopy']
        if 'formupd' in args:
            self.formupd=args['formupd']
            if self.formupd:
                self.formupd['fields']= self.formupd.get('fields',[])
                if self.formupd.get('callback'):
                    args['selectable']=self._callbackbatch
            del args['formupd']
        self.grid= SQLFORM.grid(query,formargs=dict(message_onsuccess='form accepted',
                                message_onfailure='form has errors'),**args)
        if not('edit' in self.request.args or 'view' in self.request.args or 'new' in self.request.args):
            if self.selectpaginate:
            #    if self.grid.dbset.count()>=args.get('paginate'):
                self._paginador(args.get('paginate'))
            if self.formcopy:
                self._copiador()
            if self.formupd:
                self._updater()
            if self.formadd:
                self._formadd()
        if self.rowtotals:
            offset = 1 if args.get('selectable') else 0
            grid_footer_add_totals(self.db, self.grid, query, self.fields, offset=offset)

                #el.append(SCRIPT('$(function(){%s});'%js))              
        #if len(self.request.args)<4: #esto indicaría que no está en ventana
        #    self.grid.elements('div .form_header,row_buttons',replace=None) #quitar boton atras en un add o edit
        """
        if self.grid.create_form:
            if self.grid.create_form.errors:
                self.response.flash = T('No se creó el registro')
        elif self.grid.update_form:
            if self.grid.update_form.errors:
                self.response.flash = T('No se grabó la modificación')
                redirect(URL())
            else:
                self.response.flash = T('Actualizazión guardada')
        """

    def __call__(self):
        request=self.request
        response=self.response
        table=self.grid.element('.web2py_htmltable table')
        if not('edit' in request.args or 'view' in request.args):
            if request.extension=='pdf':
                for f in self.fields:
                    if not f.readable:
                        self.fields.remove(f)
                #if not table: redirect(URL(request.function,vars=request.vars)) # por si se cuela sin tabla, aunque no es posible por programa
                self._establece_ancho_columnas(self.anchor,self.fields,table)
                if request.vars.keywords:
                    rango=request.vars.keywords
                else: rango=''
                #if request.vars.idm: rango+=(', ' if len(rango)>0 else '')+'maquina="%s"' % request.vars.idm
                #if request.vars.idc: rango+=(', ' if len(rango)>0 else '')+'entidad="%s"' % request.vars.idc
                for tab in self.db.tables:
                    rango=rango.replace(tab+'.','-')
                #rango=query_humanize(rango,'entidad',db.entidad)
                #rango=query_humanize(rango,'maquina',db.maquina)
                if rango=='':
                    rango=T('All records')
                if not self.title: self.title=T(request.function).capitalize()
                l=len(table.elements('tr'))
                if l>1000: raise HTTP(401,'Report with many records')
                return PDFtable(table,format=self.format,title=self.title,subtitle='%s: %s'% (T('Options'),rango))
            else:
                if table:
                    vars=dict(keywords=request.vars.keywords) if request.vars.keywords else None
                    printURL=URL(request.function+'.pdf',vars=request.vars,user_signature=True)
                    el=self.grid.element('.w2p_export_menu')
                    if el:
                        el.append(A('PDF',_href=printURL,_class='button btn btn-default',_target='_blank'))
        else:#se supone que estamos en el view y quito el boton atrás porque incomprensiblemente me linka a pdf, así que le den al de buscar para recargar el grid
            backpdf=self.grid.element('div .form_header')
            if backpdf:
                str=backpdf.element('a')
                str['_href']=str['_href'].replace('pdf',request.extension)
            #grid.element('div .form_header,row_buttons',replace=None) #quitar boton atras
        agrega_script_refresco(self.grid)
        return dict(grid=self.grid,title=self.title)
    def _callbackbatch(self,ids):
        if filtra_lista_request_vars(self.request.vars,'batchtype')=='upd':
            self.formupd['callback'](ids)
        elif 'formadd' in filtra_lista_request_vars(self.request.vars,'batchtype'):
            id=self.request.vars.batchtype.split('_')[1]
            self.formadd[int(id)]['callback'](ids,self.request.post_vars)
        elif 'copy' in filtra_lista_request_vars(self.request.vars, 'batchtype'):
            self.formcopy['callback'](ids)
    def _enable_all_records_selector(self):
        gridobj=self.grid
        if gridobj.elements('th') and not self._all_records_selector_enabled:  # check en cabecera para poder seleccionar todos los items de la vista
            gridobj.elements('th')[0].append(SPAN(T('All'), BR(), INPUT(_type='checkbox', _name='all_records',
                                                                        _onclick="$('input:checkbox[name=records]').not(this).prop('checked', this.checked);")))
            gridobj.elements('th')[0]['_name'] = 'checkcol'
            gridobj.elements('th')[0]['_style'] = 'display: none;'
            self._all_records_selector_enabled=True
    def _copiador(self):
        gridobj=self.grid
        bt = gridobj.element('.web2py_table input',_type='submit') #boton submit
        if bt:
            bt['_class']='ajax_btn btn btn-primary btn-default col-sm-3' #  y en color azul
            bt['_value']=T('Copiar') if self.formcopy['copy'] else T('Borrar')
            bt['_style']='display: none;'
            self._enable_all_records_selector()
        consola=gridobj.element('.web2py_console')
        for i in gridobj.elements('input[name=records]'):
            #i['_style']='display: none;'
            i.parent['_style']='display: none;'
            i.parent['_name']='checkcol'
        if consola: #meto boton toggle para mostrar/ocultar formulario copiar
            valor=''
            if self.formcopy['copy']:
                valor+=T('Copiar ')
            if self.formcopy['delete']:
                valor+=T('Borrar ')
            valor+='en lote...'
            consola.append(INPUT(_value=valor,_type='button',_class="'ajax_btn btn",_onclick="$('#formcopy').slideToggle();$('.web2py_table input:submit').slideToggle(); $('[name=checkcol]').slideToggle(); $('[name=batchtype]').val('copy');$('#formupd').hide();"))
        #formulario con los controles de copia
        if self.formcopy['delete'] :
            self.formcopy['fields'].append(Field('chkborrar', 'boolean',label='Borrar registros (no copiar)',default=False if self.formcopy['copy'] else True))
                
        form = SQLFORM.factory(_name='formcopy',*self.formcopy['fields'])
        if self.formcopy['delete'] and self.formcopy['copy']:
            form.element('[name=chkborrar]')['_onclick']='if ($(this).prop("checked")){ $(".web2py_table input[type=submit").val("Borrar");alert("Se borrarrán todos los registros seleccionados")} else {$(".web2py_table input").val("Copiar")};'
        campo=form.elements('.form-group')
        el_form=gridobj.element('div.web2py_table')
        el_form=el_form.element('form')
        if el_form:
            el_form.element('input',_type='submit',replace='')
            campo.append(DIV(_class='col-sm-3')) # esto pone a la derecha el botón
            campo.append(bt)
            campo.append(INPUT(_name='batchtype',_type='hidden'))
            el_form.insert(0,DIV(campo,_id='formcopy',_class='panel panel-info',_style='display: none'))
    
    def _updater(self):
        gridobj=self.grid
        bt = gridobj.element('.web2py_table input',_type='submit') #boton submit
        if bt:
            bt['_class']='ajax_btn btn btn-primary btn-default col-sm-3' #  y en color azul
            bt['_value']=T('Actualizar')
            bt['_style']='display: none;'
            self._enable_all_records_selector()
        consola=gridobj.element('.web2py_console')
        for i in gridobj.elements('input[name=records]'):
            #i['_style']='display: none;'
            i.parent['_style']='display: none;'
            i.parent['_name']='checkcol'
        if consola: #meto boton toggle para mostrar/ocultar formulario copiar
            valor=T('Modificar en lote...')
            consola.append(INPUT(_value=valor,_type='button',_class="'ajax_btn btn",_onclick="$('#formupd').slideToggle(); $('.web2py_table input:submit').slideToggle(); $('[name=checkcol]').slideToggle();$('[name=batchtype]').val('upd');$('#formcopy').hide();"))
        #formulario con los controles de copia
                
        form = SQLFORM.factory(_name='formupd',*self.formupd['fields'])
        campo=form.elements('.form-group')
        el_form=gridobj.element('div.web2py_table')
        el_form=el_form.element('form')
        if el_form:
            el_form.element('input',_type='submit',replace='')
            campo.append(DIV(_class='col-sm-3')) # esto pone a la derecha el botón
            campo.append(bt)
            campo.append(INPUT(_name='batchtype',_type='hidden'))
            el_form.insert(0,DIV(campo,_id='formupd',_class='panel panel-info',_style='display: none'))

    def _formadd(self):
        gridobj = self.grid
        self._enable_all_records_selector()
        consola = gridobj.element('.web2py_console')
        bt = gridobj.element('.web2py_table input', _type='submit')  # boton submit
        for frm in self.formadd:
            for i in gridobj.elements('input[name=records]'):
                # i['_style']='display: none;'
                i.parent['_style'] = 'display: none;'
                i.parent['_name'] = 'checkcol'
            idform='formadd_%s'% self.formadd.index(frm)
            if consola:  # meto boton toggle para mostrar/ocultar formulario copiar
                valor = frm['buttontext']
                consola.append(INPUT(_value=valor, _type='button', _class="'ajax_btn btn",
                 _onclick="$('#{0}').slideToggle(); $('.web2py_table input:submit').slideToggle(); $('[name=checkcol]').slideToggle();$('[name=batchtype]').val('{0}');$('#formcopy #formupd').hide();".format(idform)))
            campo = frm['form'].elements('.form-group')
            el_form = gridobj.element('div.web2py_table')
            el_form = el_form.element('form')
            if el_form:
                el_form.element('input', _type='submit', replace='')
                if bt:
                    bt['_class'] = 'ajax_btn btn btn-primary btn-default col-sm-3'  # y en color azul
                    bt['_value'] = frm['buttontext'] + T(' ahora')
                    bt['_style'] = 'display: none;'
                campo.append(DIV(_class='col-sm-3'))  # esto pone a la derecha el botón
                campo.append(bt)
                campo.append(INPUT(_name='batchtype', _type='hidden'))
                el_form.insert(0, DIV(campo, _id=idform, _class='panel panel-info', _style='display: none'))

    def _copiador_callback(self,ids):
        tabla,vars=self.formcopy.get('table'), self.request.post_vars
        if ids:
            if self.request.vars.chkborrar:
                self.db(tabla.id.belongs(ids)).delete()
                current.session.flash='Eliminados  %s registros'%(len(ids))
            else:
                for id in ids:
                    reg=tabla(id)
                    if reg:
                        del reg.id
                        try:
                            for f in  self.formcopy['fields']:
                                fieldname=f.name.split('_')[1]
                                reg[fieldname]=eval(vars.get(f.name) % reg[fieldname])
                        except:
                            self.db.rollback()
                            current.session.flash=T('Error: %s. Se canceló toda la copia')%sys.exc_info()[0]
                            redirect(self.request.url)
                        res=tabla.insert(**reg)
                        if not res.id:
                            self.db.rollback()
                            current.session.flash=res[T('Error de Copia. %s'%res.errors)]
                            return
                current.session.flash=T('Copiados  %s registros')%(len(ids))
        else:
            current.session.flash='No seleccionó ningún registro'
        redirect(URL(self.request.controller,self.request.function,vars=dict(**self.request.vars),user_signature=True))

    def _paginador(self,argspaginate):
        wt=self.grid.element('tbody','div.web2py_table')
        if wt:
            valores=[10,20,50,100,200,500]
            self.request.get_vars['paginate']='pagval'
            url=URL(self.request.controller,self.request.function,vars=dict(**self.request.get_vars),user_signature=True)
            if self.request.cid:
                js='web2py_component("%s".replace("pagval",$(this).val()),"%s");'%(url,self.request.cid)
            else:
                js='location.href="%s".replace("pagval",$(this).val());'%url
            select=SELECT(*valores,_type='sumit',_id='selectpaginate',_class='',value=argspaginate or 20,_onchange=js)
            el=self.grid.element('ul, div.web2py_paginator')
            if not el:
                if len(wt)>10:
                    el=self.grid.element('div.web2py_htmltable')
                    el.insert(2,DIV(UL(LI(select)),_class='web2py_paginator'))
            else:
                el.append(LI(select))
def agrega_refresco(campo,id,valor):
    if not ('refresh_field' in current.session):
        current.session['refresh_field']=[]
    current.session.refresh_field.append(['%s_%s_%s' % (campo._tablename, campo.name,id), valor])

def agrega_script_refresco(componente):
    js=""
    if 'refresh_field' in current.session:
        for r in current.session.refresh_field:
            js+='$("#%s").text("%s");' %(r[0],r[1])
        del current.session.refresh_field
    if js:
        componente.components.extend(TAG[''](SCRIPT('$(function(){%s});' % js)))
def agrupa_columna(grid,columna):
    el=grid.element('.web2py_table tbody')
    text=''
    grupo=''
    if el:
        for tr in el:
            if tr[columna][0]==text:
                tr[columna][0]=''
                tr['_hidegroup']=grupo
            else:
                text=tr[columna][0]
                grupo=tr['_id']
                tr[columna]=TD(SPAN(_class="icon glyphicon glyphicon-minus glyphicon-plus",_style="align: right"),tr[columna][0])
                tr[columna]['_onclick'] = '$("[hidegroup=%(gr)s]").slideToggle();$("tbody [id=%(gr)s] span").toggleClass("glyphicon-minus",1);' % dict(
                    gr=grupo)


def gridSorted_Incrementa(field, id, signo):
    """
    función que incrementa el valor del campo field, de modo que se sitúa antes o después, segú el signo, siguiendo el campo ordenado.
    sirve para procesar los campos de formulario del post de un grid que está ordenado por este campo
    y tiene activados los campos de formulario en grid para editar la ordenación
    """
    table=field._table
    orden = table(id)[field] or 0
    db=table._db
    if signo == "-":
        l = db(field < orden).select(field, orderby=~field)
        if l:
            orden = l.first()[field] - 1
    else:
        l = db(field > orden).select(field, orderby=field)
        if l:
            orden = l.first()[field] + 1
    table(id).update_record(orden_descripcion=orden)

def filtra_lista_request_vars(requestvars,clave):
    """Sirve para limpiar listas que se forman en request.vars con algunas variables que se ponen en el GEt y en el POST
    devuelve 
    """
    if clave in requestvars:
        if isinstance(requestvars[clave],(list,tuple)):
            requestvars[clave]=requestvars[clave][0]
        return requestvars[clave]
    else:
        return None
def valid_filename(cad):
    cad1= cad
    for i in '/$"#,;\&%|':
        cad1=cad1.replace(i,'_')
    return cad1
def quita_acentos(str):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ç", "c"),
        ("ñ", "n"),
        ("Á", "A"),
        ("É", "E"),
        ("Í", "I"),
        ("Ó", "O"),
        ("Ú", "U"),
        ("Ç", "C"),
        ("Ñ", "N"),
    )
    for a,b in replacements:
        str = str.replace(a, b)
    return str

def windows_popup_load(idform,function,idkey,c=None):
    idcomp='dlgform_%s'%idform
    js = 'function openform_%(idform)s(id,title){ \
              var idcomp="%(idcomp)s"+id; \
              var url="%(url)s".replace("%(idkey)s=","%(idkey)s"+"="+id); \
              if ($("#"+idcomp).length>0) { \
                $("#"+idcomp).dialog("open")}\
              else {div=$(document.createElement("DIV")); \
              $(div).attr("id",idcomp); \
              $(div).dialog({title: title, autoOpen: true, position: "center", not__modal:true, show: "fade", hide: "fade", width: 1000}); \
              $(div).dialog( "open");} \
              web2py_component(url,idcomp); \
              };' % dict(idform=idform,idkey=idkey, idcomp=idcomp,url=URL(c=c,f=function+'.load',vars={idkey:''}))
    return SCRIPT(js, _type="text/javascript")


def botones_back(request,c=None,f='index'):
    if not c:
        c=request.controller
    #boton atrás según si es página normal html o un load
    backURL=URL(c=c,f=f,vars=request.vars,user_signature=True)
    if request.extension=='html':
        return A('', SPAN(_class='icon leftarrow icon-arrow-left glyphicon glyphicon-arrow-left')
               ,_onclick='window.history.back()',_class='button btn btn-default',cid=request.cid)
    else:
        return A('',
                   SPAN(_class='icon leftarrow icon-arrow-left glyphicon glyphicon-arrow-left')
               ,_href=backURL,_class='button btn btn-default',cid=request.cid)
#FUNCIONES BASICAS


def grid_headers_align(fields):
    headers={}
    for  f in fields:
        namefield=f.__str__()
        label=f.label
        if namefield.startswith('AVG('): label=T(namefield)
        if f.type.startswith('decimal') or f.type=='integer' :
            headers[namefield]=DIV(label, _style='text-align: right;')
            #raise HTTP(404,f.label)
    return headers


class DALX(): #atajos DAL
    @classmethod
    def max(self,field,set): #devuelve el máximo de una columna de un set
        maximo=field.max()
        return set.select(maximo).first()[maximo]

    @classmethod
    def setdefault_contador(self,field,set):
        maximo = self.max(field,set)
        field.default = (maximo or 0) + 1

from gluon.sqlhtml import OptionsWidget

class SELECT_OPTIONS_JS():
    """
    Devuelve un widget normal de select options pero con un codigo javascript pegado para hacer lo que se precise
    """
    def __init__(self, js):
        self.js=js
    def widget(self, field, value):
        # generate the standard widget for this field
        select_widget = OptionsWidget.widget(field, value)
        jq_script = SCRIPT(self.js, _type="text/javascript")
        select_widget.components.extend([jq_script])
        return select_widget


def grid_addbutton(grid,title,url,confirm=True,confirm_txt=None):
    js = 'if (confirm("¿%s?")) {alert(this.text());web2py_component("%s","%s")};' % (
    confirm_txt or title, url, current.request.cid) if confirm else None
    a=A(title, _class='btn btn-success', _onclick=js)
    bt = grid['grid'].element('.web2py_console div', _type='submit')  # boton submit
    if not bt:
        bt = grid['grid'].element('.web2py_console div')  # boton submit
        if bt:
            bt.components.append(a)
    else:
        bt.parent.append(a)


def grid_addbutton_self(grid,title,url,confirm=False):
    """
    Añade botón a la consola del grid para proceso url ajax que devuelve la misma pagina
    Sirve para hacer calculos o procesos que afectan a la tabla mostrada en el grid
    :param grid:
    :param title:
    :param url:
    :param confirm:
    :return:
    """
    bt = grid['grid'].element('.web2py_console input', _type='submit')  # boton submit
    if confirm==True:
        confirm=title + '?'
    a=A(title, _class='btn btn-default',confirm= confirm ,callback=url,cid=current.request.cid,target=current.request.cid,delete='nada')
    if not bt:
        bt = grid['grid'].element('.web2py_console div')  # boton submit
        if bt:
            bt.components.append(a)
    else:
        bt.parent.append(a)
