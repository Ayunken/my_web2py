# coding: utf8
# Select or Add Option widget and Multiselect widget (al final)
from gluon import *
import os
from gluon.utils import web2py_uuid
from gluon.sqlhtml import OptionsWidget
from gluon.sqlhtml import StringWidget
import uuid
from plugin_jschosen import jschosen_widget

T=current.T
selectaddpluscount=0
class SelectOrAddOption(object):  #and even EDIT

    def __init__(self, referenced_table, controller="plugin_selectplus", function="referenced_data", dialog_width=450,select_id=None):
        self.referenced_table = referenced_table
        self.controller = controller
        self.function = function
        self.dialog_width = dialog_width
        self._my_select_id=select_id
        self.filter=filter
    def __call__(self, field, value):
        #generate the standard widget for this field
        #standar
        #select_widget = OptionsWidget.widget(field, value)
        #my_select_id = self._my_select_id or web2py_uuid()
        #my_select_id = select_widget.attributes.get('_id', None)
        #con jschosen
        select_widget = jschosen_widget(field, value)
        my_select_id = select_widget[0].attributes.get('_id', None)

        wrapper = DIV(_id=my_select_id+"__reference-actions__wrapper", _class='input-group')
        buttons=SPAN(_id=my_select_id+'_buttons',_class='input-group-btn')
        wrapper.components.extend([select_widget])
        #custom INVERCA para poner el estilo en una línea y acorde a los demás controles
        sel=wrapper.element('select',_id=my_select_id)
        sel['_class']+=' form-control'
        #sel['_style']='width:auto; display:inline;'
        #wrapper.element('select',_id=my_select_id)
        style_icons = {'new':"icon plus icon-plus glyphicon glyphicon-plus", 'edit': "icon pen icon-pencil glyphicon glyphicon-pencil" }
        actions = ['new']
        if value: actions.append('edit')  # if we already have selected value
        for action in actions:
            extra_args = [my_select_id,action,self.referenced_table._tablename ]
            if action == 'edit':
                extra_args.append(value)
            #create a div that will load the specified controller via ajax
            idcomp=my_select_id+'_'+action + '_dlgform'
            form_loader_div = DIV(_id=idcomp, _title=T(action)+": "+self.referenced_table._singular.capitalize())
            url=URL(c=self.controller,f=self.function,args=extra_args,user_signature=True)
            #generate the "add/edit" button that will appear next the options widget and open our dialog
            action_button = A([SPAN(_class=style_icons[action]), SPAN( _class="buttontext button") ],
                              _title=T(action), _id=my_select_id+"_option_%s_trigger"%action, _class="button btn btn-default", _style="vertical-align: middle" )

            #create javascript for creating and opening the dialog
            js = '$( "#%s" ).dialog({autoOpen: false, not__modal:true, show: "fade", hide: "fade", width: %s});' % (idcomp, self.dialog_width)
            js += '$( "#%(id)s_option_%(action)s_trigger" ).click(function() {   $( "#%(idcomp)s" ).dialog( "open"); web2py_component("%(url)s","%(idcomp)s"); return false;}); ' % dict(id=my_select_id, action=action, idcomp=idcomp,url=url )
            if action=='edit':
                # hide if reference changed - as load is constructed for initial value only (or would need some lazy loading mechanizm)
                js += '$(function() {$("#%s").change(function() {    $( "#%s_option_%s_trigger" ).hide(); } ) });' % (my_select_id,  my_select_id, 'edit', )
            #js para ajustar manualmente el ancho del select y que ocupe el ancho disponible, lo inyectamos solo una vez, en el add
            js='$(function(){%s});'%js
            jq_script=SCRIPT(js, _type="text/javascript")
            buttons.components.extend([action_button,form_loader_div, jq_script])
        """
        js = '$(function() {$("#%(id)s").css("width",$("#%(id)s__reference-actions__wrapper").width() - 55 -$("#%(id)s_buttons").width());' \
             '$("#%(id)s_option_new_trigger" ).css("margin-left", "+=5");}); ' % dict(id=my_select_id)
        js = SCRIPT(js, _type="text/javascript")
        """
        wrapper.components.extend([buttons])

        return wrapper

class SelectTreeWidget(object):
    _class='string form-control'
    def __init__(self, request, mptt, field, id_field=None, db=None,
                 keyword='',
                 edit_option=False, filter=None, filterdata=None,
                 field_reference_tree=None, # indica si ha de cargar como hijos de cada categoría los registros de una tabla maestra que tiene estas categorias
                 # children=[tabla, campo id relacionado con mptt, campo descripcion de tabla]
                 ):
        from plugin_jstree import JsTree
        from gluon.globals import Response
        from gluon.globals import Storage
        self.mptt=mptt #  objeto que maneja la estrucutra jerarquica para el tree
        self.request = request
        self._response = Response()
        self._response._view_environment = current.globalenv.copy()
        self._response._view_environment.update(
            request=Storage(folder=os.path.join(os.path.dirname(os.path.dirname(self.request.folder)))),
            response=self._response,
        )
        global selectaddpluscount
        self.keyword = '_tree_%(key)s_%(tablename)s_%(fieldname)s' % dict(key=keyword,
                                                                                      tablename=field._tablename,
                                                                                      fieldname=field.name
                                                                                      )
        # self.keyword='_complete_'+keyword
        self.fields = [field]
        self.edit_option = edit_option
        self.add_option_value = 0
        if self.edit_option:
            self.keyword += '_edt'
        if id_field:
            self.is_reference = True
            self.fields.append(id_field)
        else:
            self.is_reference = False
        self.fields.append(field_reference_tree)
        self.url = request
        self.db = db or field._db
        self.mptt=mptt
        self._div_id = self.keyword + '_div'
        if self.is_reference:
            self._key2 = self.keyword + '_aux'
            self._key3 = self.keyword + '_auto'
            self.jstree = JsTree(tree_model=self.mptt, renderstyle=True,edit_option=edit_option,
            selectcomponent=[self._key2, self._key3, self._div_id],table_children=self.fields if field_reference_tree else None,filter=filter,filterdata=filterdata)
        else:
            self.jstree = JsTree(tree_model=self.mptt, renderstyle=True, edit_option=edit_option, selectcomponent=[self.keyword, '', self._div_id],filter=filter,filterdata=filterdata)

    def __call__(self, field, value, **attributes):
        # ----------------------------------------------------------------------
        # SelectTreeWidget
        def script_show_parents(valor):
            if value:
                nodes = self.mptt.ancestors_from_node(valor, include_self=True).select()
                lista = "[" + (','.join([str(node.id) for i, node in enumerate(nodes)])) + "]"
                return lista
            else:
                return []
        my_select_id = '%s_%s_%s' % (field._tablename, field.name, str(uuid.uuid4())[:8])

        # generate the "dropdown" button that will appear next the options widget and open our dialog
        style_icons = {'sel': "icon pen icon-pencil glyphicon glyphicon-triangle-bottom"}
        wrapper = DIV(_id=my_select_id + "_sel_warpper", _class='form-inline')
        # ----------------------------------------------------------------------
        default = dict(
            _type='text',
            value=(not value is None and str(value)) or '',
        )
        attr = StringWidget._attributes(field, default, **attributes)
        attr['_seltree'] = 'off'
        if self.is_reference:
            url = None
            attr['_class'] = self._class
            name = attr['_name']
            if 'requires' in attr: del attr['requires']
            attr['_autoid'] = self._key2
            attr['_name'] = self._key2
            value = attr['value']
            valor = value
            if self.fields[2]: # campo tipo establece busqueda en arbol
                record = self.db(self.fields[1] == value).select(self.fields[0],self.fields[2]).first()
                valor=record and record[self.fields[2].name]
            else:
                record = self.db(self.fields[1] == value).select(self.fields[0]).first()

            attr['value'] = record and record[self.fields[0].name]

            attr['_onblur'] = "if ($('#%s').val())" \
                              "div_Show('%s',false);" % (self._key3,self._div_id)
            attr['_onfocus'] = "div_Show('%s',true);" % self._div_id
            # attr['_style']='width:80%;'
            # button action
            actions = ['sel']
            action_button = SPAN(_id=my_select_id + '_buttons',
                                 *[A([SPAN(_class=style_icons[action]), SPAN(_class="buttontext button")],
                                     _title=T(action), _id=my_select_id + "_option_%s_trigger" % action,
                                     _class="button btn btn-default", _style="vertical-align:middle") for action in
                                   actions])
            dic = dict(key=self.keyword,
                       id=attr['_id'], key2=self._key2, key3=self._key3,
                       name=name,
                       div_id=self._div_id,
                       field=self.fields[0].name,
                       script_show_parents=script_show_parents(valor),
                       edit=self.edit_option,
                       my_select_id=my_select_id,
                       fileid=value if self.fields[2] else '')
            jq_script = XML(self._response.render('plugin_selectplus/selectplus_tree_js.html', dic))
            wrapper.components.extend([TAG[''](INPUT(**attr), action_button,
                                               INPUT(_type='hidden',
                                                     _id=self._key3,
                                                     _value=value,
                                                     _name=name,
                                                     requires=field.requires),
                                               DIV(self.jstree(),_id=self._div_id,
                                                   _style='padding: 12 0 0 0px;position:absolute;'),
                                               jq_script)])
            return wrapper
        else: #sin reference, no id
            attr['_name'] = field.name
            attr['_autoid'] = self.keyword
            attr['_onblur'] = "jQuery('#%s').delay(500).fadeOut();" % self._div_id
            attr['_class'] = self._class
            dic = dict(key=self.keyword, id=attr['_id'], div_id=self._div_id, key2=self.keyword,
                       field=self.fields[0].name,
                       my_select_id=my_select_id)
            jq_script = XML(self._response.render('plugin_selectplus/selectplustree_js.html', dic))
            wrapper.components.extend([TAG[''](INPUT(**attr),
                                               DIV(self.jstree(),_id=self._div_id,
                                                   _style='padding: 12 0 0 0px;position:absolute;')),
                                       jq_script])
            return wrapper


class AutocompleteWidgetSelectOrAddOption(object):
    _class = 'string form-control'

    def __init__(self, request, field, id_field=None, db=None,
                 orderby=None, maxresults=10,
                 keyword='',
                 min_length=2,
                 # -------------------------------------------------------------
                 # SelectOrAddOption
                 controller='plugin_selectplus',
                 function='referenced_data',
                 form_title=None,
                 button_text = None, dialog_width=1000,
                 multi=False,sep='@ ',
                 add_option=True
                 # -------------------------------------------------------------
                 ):
        self.request = request
        from gluon.globals import Response
        from gluon.globals import Storage
        self._response = Response()
        self._response._view_environment = current.globalenv.copy()
        self._response._view_environment.update(
            request=Storage(folder=os.path.join(os.path.dirname(os.path.dirname(self.request.folder)))),
            response=self._response,
        )
        global selectaddpluscount
        self.keyword='_complete_%(key)s_%(dif)s_%(tablename)s_%(fieldname)s' % dict(key=keyword,tablename=field._tablename,fieldname=field.name,dif=request.args[-1] if len(request.args) else '')
        #self.keyword='_complete_'+keyword
        self.db = db or field._db
        self.orderby = orderby or field
        self.maxresults = maxresults
        self.offset=0
        self.min_length = min_length
        self.fields=[field]
        self._multi=multi
        self._sep=sep
        self.controller=controller
        self.function=function
        self.dialog_width = dialog_width
        self.add_option=add_option
        self.add_option_value=0
        if self.add_option:
            self.keyword+='_add'
        if id_field:
            self.is_reference = True
            self.fields.append(id_field)
        else:
            self.is_reference = False
        if hasattr(request,'application'):
            self.url = URL(args=request.args)
            url=self.url
            self.callback()
        else:
            self.url = request

        # ----------------------------------------------------------------------
        # SelectOrAddOption
        if form_title == None:
            self.form_title = self.db[self.fields[0]._tablename]._singular
        else:
            self.form_title = T(form_title)
        if button_text == None:
            self.button_text = T('Add')
        else:
            self.button_text = T(button_text)

        # ----------------------------------------------------------------------
    def callback(self):
        if self.keyword in self.request.vars:
            field = self.fields[0]
            self.offset=int(self.request.vars.pg or 1)-1
            rows = self.db(field.like('%'+self.request.vars[self.keyword]+'%'))\
                .select(orderby=self.orderby,
                        limitby=(self.offset,self.maxresults+self.offset),*self.fields)
            #Tuve que poner el  decode-encode para que no muestre caracteres no ingleses como interrogantes en un rombo
            if '_add' in self.keyword:
                if self.is_reference:
                    Add=[OPTION('--%s "%s"'%(T('Add'),self.request.vars[self.keyword].decode('latin-1').encode('utf8')),_value=self.add_option_value,_id='selectadd')]
                else:
                    Add=[OPTION('--%s "%s"'%(T('Add'),self.request.vars[self.keyword].decode('latin-1').encode('utf8')), _id='selectadd')]
            else:
                Add=[]
            if rows:
                if self.is_reference:
                    id_field = self.fields[1]
                    opciones=[OPTION(s[field.name],_value=s[id_field.name],_selected=(k==0))  for k,s in enumerate(rows)]
                else:
                    opciones=[OPTION(s[field.name],_selected=(k==0)) \
                                          for k,s in enumerate(rows)]
                if len(rows) == self.maxresults:
                    opciones += [OPTION('Más>>',_class='icon glyphicon glyphicon-arrow-down',_value=-(self.offset+self.maxresults+1),_id='selectnext')]
                if self.offset >0:
                    opciones = [OPTION('<<Menos',_class='icon glyphicon glyphicon-arrow-up', _value=-(self.offset - self.maxresults+1), _id='selectprev')]+opciones
                opciones+=Add
                raise HTTP(200,SELECT(_id=self.keyword,_class='autocomplete',
                                          _size=len(opciones),_multiple=(len(rows)==1),
                                          *opciones).xml())
            else:

                raise HTTP(200,SELECT(_id=self.keyword,_class='autocomplete',
                                          _size=len(Add),_multiple=True,
                                          *Add).xml())
    def __call__(self,field,value,**attributes):
        # ----------------------------------------------------------------------
        # SelectOrAddOption
        my_select_id = '%s_%s_%s' % (field._tablename, field.name,str(uuid.uuid4())[:8])
        
        #create a div that will load the specified controller via ajax
        idcomp=my_select_id+"_dialog-form"
        form_loader_div = DIV(_id=idcomp, _title=self.form_title)
        #generate the "add" button that will appear next the options widget and open our dialog
        style_icons = {'add':"icon plus icon-plus glyphicon glyphicon-plus", 'edit': "icon pen icon-pencil glyphicon glyphicon-pencil" }
        wrapper = DIV(_id=my_select_id+"_adder_wrapper")
        # ----------------------------------------------------------------------
        default = dict(
            _type = 'text',
            value = (not value is None and str(value)) or '',
            )
        attr = StringWidget._attributes(field, default, **attributes)
        div_id = self.keyword+'_div'
        attr['_autocomplete']='off'
        if self.is_reference:
            key2 = self.keyword+'_aux'
            key3 = self.keyword+'_auto'
            if self.add_option:
                add_args = [key3,'new',self.fields[0]._tablename] #esto sería si una funcion del controlador maneja esto
                urladd=URL(c=self.controller,f=self.function,args=add_args,user_signature=True)
                add_args=[key3,'edit',self.fields[0]._tablename,value]
                urledit=URL(c=self.controller,f=self.function,args=add_args,user_signature=True)
            else:
                url=None
            attr['_class']=self._class
            name = attr['_name']
            if 'requires' in attr: del attr['requires']
            attr['_autoid'] = key2
            attr['_name']=key2
            value = attr['value']
            record = self.db(self.fields[1]==value).select(self.fields[0]).first()
            attr['value'] = record and record[self.fields[0].name]
            attr['_onblur']="jQuery('#%(div_id)s').delay(500).fadeOut();" % \
                dict(div_id=div_id,u='F'+self.keyword)
            #attr['_style']='width:80%;'
            #button action
            actions = ['add']
            if value: actions.append('edit')
            action_button = SPAN(_id=my_select_id+'_buttons',_class='input-group-btn',*[A([SPAN(_class=style_icons[action]), SPAN( _class="buttontext button") ],
                 _title=T(action), _id=my_select_id+"_option_%s_trigger"%action, _class="button btn btn-default", _style="vertical-align:middle" ) for action in actions])
            dic=dict(url=self.url,
                         min_length=self.min_length,
                         key=self.keyword,
                         id=attr['_id'],key2=key2,key3=key3,
                         name=name,
                         div_id=div_id,
                         u='F'+self.keyword,
                         idcomp=idcomp,
                         urlcomp=urladd,urledit=urledit,
                         field=self.fields[0].name,
                         my_select_id=my_select_id,
                         dialog_width=self.dialog_width,
                        tablename=self.db[self.fields[0]._tablename]._singular)
            jq_script=XML(self._response.render('plugin_selectplus/selectplus_js.html',dic))
            if self.min_length==0:
                attr['_onfocus'] = attr['_onkeyup']
            wrapper.components.extend([DIV([INPUT(**attr),action_button,
                                      INPUT(_type='hidden',_id=key3,_value=value,_name=name,requires=field.requires)],_class='input-group'),
                                      DIV(_id=div_id,_style='padding: 12 0 0 0px;position:absolute;'),
                                      form_loader_div,jq_script])
            return wrapper
        else:
            if self.add_option:
                add_args = [my_select_id,'new',self.fields[0]._tablename]
                urladd=URL(c=self.controller,f=self.function,args=add_args,user_signature=True)
                add_args= [my_select_id,'edit',self.fields[0]._tablename,value]
                urledit=URL(c=self.controller,f=self.function,args=add_args,user_signature=True)
            else:
                urladd=None
                urledit=None
            attr['_name']=field.name
            attr['_autoid'] =self.keyword
            attr['_onblur']="jQuery('#%(div_id)s').delay(500).fadeOut();" % \
                dict(div_id=div_id,u='F'+self.keyword)
            attr['_class']=self._class
            dic=dict(url=self.url,min_length=self.min_length,
                     key=self.keyword,id=attr['_id'], div_id=div_id,key2=self.keyword,
                     u='F'+self.keyword,idcomp=idcomp,urlcomp=urladd,urledit=urledit,
                     field=self.fields[0].name,sep=self._sep,
                     my_select_id=my_select_id,
                     dialog_width=self.dialog_width,
                    tablename=self.db[self.fields[0]._tablename]._singular)
            if self._multi:
                jq_script=XML(self._response.render('plugin_selectplus/selectplus3_js.html',dic))
            else:
                jq_script=XML(self._response.render('plugin_selectplus/selectplus2_js.html',dic))
            if self.min_length==0:
                attr['_onfocus'] = attr['_onkeyup']
            wrapper.components.extend([TAG[''](INPUT(**attr),
                                      DIV(_id=div_id,
                                      _style='padding: 12 0 0 0px;position:absolute;')),
                                      form_loader_div,jq_script])
            return wrapper


"""
# Multiselect widget from http://www.web2pyslices.com/slice/show/1395/jquery-multi-select-widget
#Definir un campo de esta manera:
 db.tabla.campo.requires = IS_IN_SET(['Apples','Oranges','Bananas','Kiwis','Lemons'],multiple=True)
#y asignarle el widgget
 db.tabla.campo.widget = multiselect_widget
 Si se quiere un select condicionado a otro combo, usar pluging_lazy_options_widget
"""
def multiselect_widget(f,v):
    from gluon import current
    #multi select normal con 1 select donde se sombrea cada item.
    current.response.files.append(URL(r=request,c='static/ui/multiselect',f='jquery.multiselect.css'))
    current.response.files.append(URL(r=request,c='static/ui/multiselect',f='jquery.multiselect.min.js'))
    #multi select con 2 ventana de seleccionados y no seleccionados
    #current.response.files.append(URL(r=request,c='static/ui/multi-select',f='jquery.multi-select.css'))
    #current.response.files.append(URL(r=request,c='static/ui/multi-select',f='jquery.multi-select.js'))
    d_id = "multiselect-" + str(uuid.uuid4())[:8]
    wrapper = DIV(_id=d_id)
    inp = SQLFORM.widgets.options.widget(f,v)
    inp['_multiple'] = 'multiple'
    inp['_style'] = 'min-width: %spx;' % (len(f.name) * 20 + 50)
    if v:
        if not isinstance(v,list): v = str(v).split('|')
        opts = inp.elements('option')
        for op in opts:
            if op['_value'] in v:
                op['_selected'] = 'selected'
    scr = SCRIPT('jQuery("#%s").multiselect({'\
                 'maxItems: -1, defaultDisplayTitle: "Select %s"});' % (d_id,f.name))
    wrapper.append(inp)
    wrapper.append(scr)
    if request.vars.get(inp['_id']+'[]',None):
        var = request.vars[inp['_id']+'[]']
        if not isinstance(var,list): var = [var]
        request.vars[f.name] = var
        del request.vars[inp['_id']+'[]']
    return wrapper

"""
# MultiTab UI constructor
 necesita cargar jquery UI
 tabs=matriz de ['DenTab',{loadURL}],
 {laodURL}={'c': controller, 'f': function, user_signature=False,vars=vars), que se le pasan por el **tabs[x][1]
"""

def multiTab_widget(tabs,active=0,tab_id=None):
    tab_id=tab_id or web2py_uuid()
    wp=DIV(_id=tab_id)
    sc ='$(function(){ $("#%s").tabs(); '% tab_id
    sc+='$("#%s").tabs({activate: function( event, ui ) {switch (ui.newPanel.attr("id")){' % tab_id
    for x in range(0,len(tabs)):
        if not 'content' in tabs[x][1]: #si no lleva contenido directo, se usa url de ajax
            id='%s-%s'%(x,tab_id)
            url=URL(**tabs[x][1])
            sc+='case "%s": web2py_component("%s","%s"); break;' %(id,url,id)
    sc+='}}});});'
    wp.components.extend([SCRIPT(sc, _type="text/javascript")])
    onmouseover='for (i = 0; i < %(ntabs)s; i++) { $("#"+i+"-%(tab_id)s").hide();} \
    $("#%(ntab)s-%(tab_id)s").show();'
    #_onmouseover=onmouseover % dict(tab_id=tab_id,ntab=x,ntabs=len(tabs))
    wp.components.extend([UL(*[LI(A(tabs[x][0],_href='#%s-%s' % (x,tab_id))) for x in range(0,len(tabs))])])
    for x in range(0,len(tabs)):
        ld=P(T('loading...'))
        if x==active and not 'content' in tabs[x][1]:
            ld=LOAD(ajax=True,target='%s-%s'%(x,tab_id),**tabs[x][1])
        elif 'content' in tabs[x][1]:
            ld=tabs[x][1]['content']
        wp.components.extend([DIV(ld,_id='%s-%s'%(x,tab_id))])
    return wp

def autoSugest_widget(): # no usado, esto está a mitad de hacer: usar el
    from gluon import current
    response=current.response
    response.files.append(URL(r=request,c='static/textboxlist',f='textboxlist.css'))
    response.files.append(URL(r=request,c='static/textboxlist',f='textboxlist_autocomplete.css'))
    response.files.append(URL(r=request,c='static/textboxlist',f='growinginput.js'))
    response.files.append(URL(r=request,c='static/textboxlist',f='textboxlist.js'))
    response.files.append(URL(r=request,c='static/textboxlist',f='textboxlist_autocomplete.js'))
    response.files.append(URL(r=request,c='static/textboxlist',f='textboxlist_bin.js'))


def selectaddplus_close_dialog(response, request, form,db):    
    references_options_list_id = request.args[0]
    action = request.args[1]
    referenced_table= request.args[2]
    if form.accepts(request.vars):
        #Then let the user know adding via our widget worked
        response.flash = T('done: %s %s') %( T(action),  referenced_table) # added / edited
        #close the widget's dialog box
        response.js = '$( "#%s" ).dialog( "close" ); ' %(request.cid)

        def format_referenced(id):
            #return format(db[referenced_table], id)  #should get from table
            table = db[referenced_table]
            if isinstance(table._format, str):     return table._format % table[id]
            elif callable(table._format):          return table._format(table[id])
            else: return "???"
        elaux=references_options_list_id.replace('_auto','_aux')
        if action=='new':
            #update the options they can select their new category in the main form
            response.js += """
            if ($('#%(elid)s')[0].tagName=="SELECT"){
            $('#%(elid)s').append('<option value="%(id)s">%(name)s</option>');}
            else {
            $('#%(elaux)s').val('%(name)s');};
            """ % (dict(elid=references_options_list_id, id=form.vars.id, name=format_referenced(form.vars.id), elaux=elaux))
            #and select the one they just added
            response.js += """$("#%s").val("%s");""" % (references_options_list_id, form.vars.id)
        if action=='edit':
            #response.js += """alert( $('#%s option[value="%s"]').html());""" % (references_options_list_id, form.vars.id) # format_referenced(form.vars.id) )
            response.js += """$("#%(elid)s option[value='%(id)s']").html("%(name)s");""" % dict(elid=references_options_list_id, id=form.vars.id, name= format_referenced(form.vars.id) )
        if  references_options_list_id[-5:]=='_auto':
            response.js += '$("[name=%s]").val("%s");' % (elaux, format_referenced(form.vars.id))
