#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
import datetime
from gluon import current
T=current.T
import sys, re

class MOD_ATR_TIPO():
    formula='F'
    valores='V'
    @classmethod
    def getitems(self):
        return {self.formula:'Formula',self.valores:'Valores discretos'}

class MOD_CMP_TIPO():
    pieza='P'
    modulo='M'
    @classmethod
    def getitems(self):
        return {self.pieza:'Pieza',self.modulo:'Módulo'}

FORMULAS_SEPARADORES='[]'
FORMULAS_REGEXPR="\[[^\[]*\]"
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
    def __init__(self,funcion,triggers,keyword='_compute_lazy_%(fieldname)s',user_signature=False,hmac_key=None,visible=True):
        self.funcion,self.triggers,self.keyword,self.user_signature,self.hmac_key,self.visible= funcion,triggers,keyword,user_signature,hmac_key,visible
        if not isinstance(triggers,(list,tuple)):
            self.triggers=[triggers]
        self._triggers=(', '.join(['#%s_%s' %(i._tablename,i.name) for i in self.triggers]))

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
        if self._require:
            wd=options_widget(field, value,**attributes)
        else:
            wd=string_widget(field, value,**attributes)
        wd['_class']='generic-widget form-control'
        self._el_id = '%s_%s' % (field._tablename, field.name)
        if self.visible==False:
            jsocultar='$("#%s__row").hide();' % self._el_id
        else:
            jsocultar=''
        js=SCRIPT("""
$("%(triggers)s").change(function(e){
           var query = {};
           var val=$( this ).val();
           query["%(keyword)s"] = this.id;
           query[this.id]=val;
           $.ajax({type: "POST", url: "%(url)s", data: query,
            success: function(value) {$("#%(el_id)s").val(value);$("#%(el_id)s").change();
            }})});
%(jsadd)s

""" % dict(triggers=self._triggers,url=self.url,el_id=self._el_id,keyword=self._keyword,jsadd=jsocultar))
        return DIV(wd,js)

class IS_FORMULA(object):
    def __init__(self, db, field_variables, error_message=T('Formula incorrecta: ')):
        self.db=db
        self.field_variables=field_variables
        self.table=field_variables._tablename
        self.e = error_message
    def _validate(self,value):
        lista = IS_FORMULA.lista_vars(value)
        errores=''
        variables={}
        for key in lista:
            row=self.db(self.field_variables==key).select()
            if row:
                variables[key]=row[0].id # le pongo un valor para que la evaluación de un resultado
            else:
                errores+=T('%satributo %s no existe') % (',' if errores else '',key)
        if errores:
            self.e+=errores
            return False
        formula=value.replace(FORMULAS_SEPARADORES[0],'%(').replace(FORMULAS_SEPARADORES[1],')s') #cambia los corchetes por %(key)s para que se pueda formatear con el diccionario al evaluar
        try:
            a=eval(formula % variables)
            formula=value.replace(FORMULAS_SEPARADORES[0],FORMULAS_SEPARADORES[0]+'%(').replace(FORMULAS_SEPARADORES[1],')s'+FORMULAS_SEPARADORES[1])
            return (formula % variables)
        except:
            self.e+=sys.exc_info()[0]
            return False

    def __call__(self, value):
        ret=self._validate(value)
        if ret:
            return ret, None
        return (value, self.e)
    def formatter(self, value):
        return  IS_FORMULA.formatea(self.db,value,self.field_variables)
    @staticmethod
    def lista_vars(cadena):
        if cadena:
            regex = re.compile(FORMULAS_REGEXPR)  # busca cadenas de texto que empiezen por [ (no sigan por '[' ) y acaben en ']'
            lista=regex.findall(cadena)
            for k  in range(0,len(lista)):
                lista[k]=lista[k].replace(FORMULAS_SEPARADORES[0],'').replace(FORMULAS_SEPARADORES[1],'')
            return lista
        else:
            return []
    @staticmethod
    def formatea(db,value,field_variables):
        table=field_variables._tablename
        if value:
            lista=IS_FORMULA.lista_vars(value)
            errores=''
            variables={}
            for key in lista:
                row=db[table](key)
                if row:
                    variables[key]=row[field_variables.name] # y o cambiamos por el nombre clave de la variable
                else:
                    variables[key]=key
            formula=value.replace(FORMULAS_SEPARADORES[0],FORMULAS_SEPARADORES[0]+'%(').replace(FORMULAS_SEPARADORES[1],')s'+FORMULAS_SEPARADORES[1])
            return  (formula % variables)
        else:
            return ''

class GRAL(): #constantes globales propias
    #opciones predeterminadas para SQLFORM.grid
    dateFmt='%d/%M/%Y'
    timeFmt='%d/%h/%y %H:%m'
    dateFormat=current.T(dateFmt)
    dateError=current.T('Must be DD/MM/YYYY!')
    currency_simbol='€'
    labelcompany='INVERCA'
    grid_defaults={'exportclasses': dict(xml=False,json=False,tsv=False,tsv_with_hidden_cols=False,csv_with_hidden_cols=False),
                   'maxtextlength': 30,
                   'showbuttontext': False,
                   'paginate': 20,
                   'links_in_grid': True,
                   'details': False,
                   #'ui': 'jquery-ui'
                  }
    #opciones predeterminadas añadidas para PDFS de SQLFORM.grid
    grid_adddefaults_pdf={'paginate': 500,
                          'csv': False,
                          'details': False,
                          'links_in_grid': False
                          }
    grid_pdf_defaults=grid_defaults.copy()
    grid_pdf_defaults.update(grid_adddefaults_pdf)
    def represent_currency(self, value):
        if value == None:
            return DIV('-',_style='text-align: right;')
        else:
            return DIV('%.2f%s' %  ((0 if value==None else value), self.currency_simbol), _style='text-align: right;')


    def fechaq(self,fecha):
        return datetime.date(fecha.year,fecha.month,fecha.day)

def botones_back(request,c='default',f='index'):
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

def valNum(var):
    try: return float(var)
    except: return 0

def valStr(var):
    return '' if var is None else var

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

def grid_footer_align(fields,values):
    footer=[]
    for  f in fields:
        namefield=f.__str__()
        if values.has_key(namefield):
            if (f.type=='decimal(9,2)') :
                footer.append(TH(VDC().represent_currency(values[namefield]),_align='right'))
            elif (f.type.startswith('decimal') or f.type=='integer'):
                footer.append(TH(values[namefield], _align='right'))
        else:
            footer.append(TH(' '))
    return footer

def grid_footer_add_totals(db,grid,query,fields,left=None):
    '''
    Agrega Totales segun la lista de campos de fields
    Totaliza todos los campos que se ha añadido el atributo ..field._extra={'total':True}
    '''
    request=current.request
    s=[]
    pies={}
    for f in fields:
        if hasattr(f,'_extra'):
            if f._extra['total']:
                if f.name.endswith('*sum'):
                    s.append(db[f.tablename][f.name.split('*')[0]].sum())
                else:
                    s.append(f.sum())
    if s:
        if  'keywords'  in request.vars:
            if len(request.vars.keywords)>0:
                query=(query) & (request.vars.keywords)
        row= db(query).select(*s, left=left).first()
        for f in fields:
            if hasattr(f,'_extra'):
                if f._extra['total']:
                    if f.name.endswith('*sum'):
                        pies[f.__str__()]=row[db[f.tablename][f.name.split('*')[0]].sum()]
                        if f.__str__().startswith('AVG('):
                            pies[f.__str__()]=None #row[db[f.tablename][f.name.split('*')[0]].count()]
                        #ya es un sumatorio, no voy a sumar la suma de sumas
                    else:
                        pies[f.__str__()]=row[f.sum()]
                        #pies[f.__str__()]=row[f._extra['field_summed'].sum()]
    if pies and grid.element('.web2py_htmltable tbody'):
        grid.element('.web2py_htmltable tbody').append((TR(grid_footer_align(fields,pies) ,_id='tot_gral')))

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

def grid_create_sumfields(oper='sum',fields=''):
    """
    Crea una lista de campos sumatorios para añadir a la lista de campos
    de un query y poder usarlos para sumar un grid con groupby
    """
    res=[]
    for f in fields:
        count={'count':f.count(),'sum':f.sum(), 'avg':f.avg(),'min':f.min(),'max':f.max()}[oper]
        count.tablename = f.tablename
        count.name=f.name + '*sum'
        count.readable = True
        count.type=f.type #'decimal(9,2)'
        count.label=DIV(f.label, _style='text-align: right;') #ya le arreamos justificar a la derecha para la etiqueta
        count.represent=f.represent
        count.formatter =lambda value:value
        count.table = f.table
        count._extra={'total':True} #,'field_summed':f} #esto es para grid_footer_add_totalesm así sabe el campo sumado
        res.append(count)
    return res

def report_fields_list(db):
    """ Lista de campos de cada informe """
    return {'mod_atr':[db.mod_atr.name, db.mod_atr.clave,db.mod_atr.grp_atr, db.mod_atr.tipo, db.mod_atr.val_def_disp, db.mod_atr.um, db.mod_atr.rango_disp]
                }


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



class Input_compute_in_form(object):  #and even EDIT
    """ Devuelve codigo javascript que calcula el valor del campo  mediante la funcion javascript pasada en 'function'
        e.g.: function='$("[name=\'name\']").val().substring(0,20)'  # copia el campo 'name' y lo recorta a 20 caracteres
    """
    def __init__(self,  function):
        self._funcion=function

    def __call__(self,field,value,**attributes):
        from gluon.sqlhtml import StringWidget
        default = dict(
            _type = 'text',
            value = (not value is None and str(value)) or '',
            )
        attr=StringWidget._attributes(field, default, **attributes)
        attr['_class'] = 'form-control string'
        wrap=DIV()
        wrap.components.extend(TAG[''](INPUT(**attr),
                     SCRIPT('$("[name=\'%s\']").focusin(function(e) {if ($(this).val().length==0) $(this).val(%s);});' %  (attr['_name'], self._funcion))))
        return wrap
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
        self.format='L'
        self.response=current.response
        self.request=current.request
        if 'fields' in args:
            self.fields=args['fields']
        else:
            self.fields=[[f] for f in query.fields]
        if 'title' in args:
            self.title=args['title']
            del args['title']
        if 'anchor' in args:
            self.anchor=args['anchor']
            del args['anchor']
        if 'format' in args:
            self.format=args['format']
            del args['format']
        if  not ('formname' in args):
            import uuid
            args['formname']='%s'% (self.request.function) #,str(uuid.uuid4())[:8])

        self.grid= SQLFORM.grid(query,formargs=dict(message_onsuccess='form accepted',
                                message_onfailure='form has errors'),onvalidation=myFormValidation,**args)

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
                    self.grid.element('.w2p_export_menu').append(A('PDF',_href=printURL,_class='button btn btn-default',_target='_blank'))
        else:#se supone que estamos en el view y quito el boton atrás porque incomprensiblemente me linka a pdf, así que le den al de buscar para recargar el grid
            backpdf=self.grid.element('div .form_header')
            if backpdf:
                str=backpdf.element('a')
                str['_href']=str['_href'].replace('pdf',request.extension)
            #grid.element('div .form_header,row_buttons',replace=None) #quitar boton atras
        return dict(grid=self.grid,title=self.title)



def record_validator(tabla,r,s=None,form=None):
    #esta rutina igual sirve para el validador de registro de SQLFORM que para el validador de table _before_update/before_insert
    def validate_duplicates(query,s=None):
        if s:
            query=(query) & (tabla.id!=s['id'])
        query=tabla._db(query).select()
        if query:
            return True
    tablename=tabla._tablename
    if tablename=='mod_val':
        mod_atr_id=r['atr'] if r['atr'] else  tabla.atr.default
        return validate_duplicates((((tabla.name==r['name']) | (tabla.valor==r['valor']) )  & (tabla.atr==mod_atr_id)),s)
    elif tablename=='mod_cmp':
        mod_id=r['mod'] if r['mod'] else tabla.mod.default
        if str(mod_id)==str(r['cmp_mod']):
            error=T('Un módulo no puede ser componente de sí mismo')
            if form:
                form.errors.cmp_mod=error
            else:
                current.session.flash=error
            return False
        if not r['cmp_mod'] and r['cmp_tipo']==MOD_CMP_TIPO.modulo:
            error=T('Módulo no puede estar vacío')
            if form:
                form.errors.cmp_mod=error
            else:
                current.session.flash=error
            return False
        if not r['cmp_pie'] and r['cmp_tipo']==MOD_CMP_TIPO.pieza:
            error=T('Pieza no puede estar vacío')
            if form:
                form.errors.cmp_pie=error
            else:
                current.session.flash=error
            return False
        return validate_duplicates((((tabla.cmp_pie!=None) | (tabla.cmp_mod!=None )) & (tabla.mod==mod_id) & (tabla.cmp_pie==r['cmp_pie'])  & (tabla.cmp_mod==r['cmp_mod']) & (tabla.cmp_tipo==r['cmp_tipo'])),s)
    elif tablename=='mod_mod_atr':
        mod_id=r['mod'] if r['mod'] else  tabla.mod.default
        if r['tipo']==MOD_ATR_TIPO.valores and r['valores']:
            if not (str(r['val_def']) in r['valores']):
                if form: form.errors.val_def=T('No está en rango de valores')
                return False
        return validate_duplicates((tabla.atr==r['atr'])  & (tabla.mod==mod_id),s)

def myFormValidation(form):
    #raise HTTP(400,BEAUTIFY(db))
    if record_validator(form.table,form.vars,form.record,form):
            form.errors[0]='Error'
            current.response.flash=T('Valor ya existente en la base de datos')

def recolectar_atributos_modulo(db,mod_id):
    def combina_atributos(atr1,atr2):
        if atr1['atr']==atr2['atr']:
            atr=atr1
            if atr1['tipo']==MOD_ATR_TIPO.valores:
                atr['valores'] = [ x for x in atr1['valores'] if x in atr1['valores']]
                if not atr['val_def'] in atr['valores']:
                    atr['val_def']=atr2['val_def']
                elif len(atr['valores'])>0:
                    atr['val_def']=atr['valores'][0]
            else:
                #atr['rango']  POR AHORA LOS DEJO TAL CUAL EL PRIMERO, PERO HABRA QUE HALLAR UN ALGORITMO QUE PERMITA COMBINAR RANGOS EN MODO ABREVIADO
                #atr['val_def_formula']
                pass
            return atr

    if not db.mod(mod_id): return
    atributos=[]
    atributos_data={}
    #atributos de módulos componentes
    Modatr2=db.mod_mod_atr.with_alias('modatr2')
    row=db((db.mod_cmp.mod==mod_id) & (db.mod_cmp.cmp_mod>0)).select(db.mod_mod_atr.ALL,left=db.mod_mod_atr.on(db.mod_mod_atr.mod==db.mod_cmp.cmp_mod))
    if row:
        for x in row:
            v=x['atr']
            if not (v in atributos):
                atributos.append(v)
                atributos_data[v]=x
            else:
                atributos_data[v]=combina_atributos(atributos_data[v],x)
    #atributos usados en fórmulas de componentes
    rows=db(db.mod_cmp.mod==mod_id).select(db.mod_cmp.formula)
    if rows:
        for r in rows:
            lista=IS_FORMULA.lista_vars(r['formula'])
            if lista:
                for v in lista:
                    if not v in atributos:
                        atributos.append(v)
    #GUARDAR ATRIBUTOS
    if atributos:
        return atributos,atributos_data
        db((db.mod_mod_atr.lock==False) & (db.mod_mod_atr.mod==mod_id)).delete()
        for ida in atributos:
            if not ida in atributos_data:
                atr=db.mod_atr(ida)
                for i in ['tipo','atr','val_def','val_def_formula']:
                    atributos_data[ida][i]=atr[i]
                v=db.mod_val(db.mod_val.atr==ida).select(fields=db.mod_val.id)
                if v:
                    atributos_data[ida]['valores']=(', '.join(i['id'] for i in v))
                    if not atributos_data[ida]['val_def']:
                        atributos_data[ida]['val_def']=atributos_data[ida]['valores'][0]
            atributos_data['lock']=False
            #del atributos_data['id']
            modatr=db((db.mod_mod_atr.atr==ida) & (db.mod_mod_atr.mod==mod_id )).select()
            if modatr:
                modatr.update(**atributos_data[ida])
            else:
                db.mod_mod_atr.insert(**atributos_data[ida])
