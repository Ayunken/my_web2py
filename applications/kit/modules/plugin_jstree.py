# -*- coding: utf-8 -*-
# This plugins is licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
# Authors: Yusuke Kishita <yuusuuke.kishiita@gmail.com>, Kenji Hosoda <hosoda@s-cubism.jp>
from gluon import *
from gluon.contrib import simplejson as json
# For referencing static and views from other application
import os
APP = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
import gluon.contenttype

class JsTree(object):
    
    def __init__(self, tree_model, renderstyle=False,version=3,search=False,selectcomponent=[],keyword=None,
                 user_signature=True, edit_option=True,
                 hmac_key=None,
                 onsuccess=None,  # def onsuccess(affected_node_ids): ...
                 table_children=[], filter=None, filterdata=None, count_descendants=True
                 ):
        self.tree_model = tree_model  # tree_model could be an MPTT object of plugin_mptt
        
        _urls = [URL(APP, 'static', 'plugin_jstree/jstree_%s/jquery.hotkeys.js' % version ),
                 URL(APP, 'static', 'plugin_jstree/jstree_%s/jquery.jstree.js' % version )]
        if renderstyle:
            _urls.append(URL(APP, 'static', 'plugin_jstree/main.css'))
        if version==3:
            _urls.append(URL(APP,'static','plugin_jstree/jstree_3/themes/default/style.min.css'))
        for _url in _urls:
            if _url not in current.response.files:
                current.response.files.append(_url)
        # Para modo select, simplemente pasar en selectcomponent con 3 items: ["idtextDescription","idtextId","idcontenedor"]
        # si no lleva referencia, el 2 pasarlo en blanco, pero que haya 3
        # Para mode cargar un div mediante web2py_component: selectcomponent=["url..?node_id","divid"]
        # node_id será reemplazado por el valor del id del nodo
        self._idcontainer = ''
        if selectcomponent:
            self._urlcomponent=selectcomponent[0]
            self._idcomponent=selectcomponent[1]
            if len(selectcomponent)==3:
                self._idcontainer=selectcomponent[2]
        else:
            self._idcomponent=self._urlcomponent=''
        self._children=table_children
        self._version=version
        self._search=search
        self._keyword=keyword or ('jstree'+ self._idcomponent)
        self._request = current.request
        self.filter=filter
        self.filterdata=filterdata
        self.count_descendants=count_descendants
        if self._keyword in self._request.args and self._request.args[-1]:
            self._callback(self._request, user_signature, hmac_key, onsuccess=None)
        self._user_signature=user_signature
        self._hmac_key=hmac_key
        self._edit_option=edit_option

    def recordbutton(self, buttonclass, buttontext, buttonurl, showbuttontext=True, **attr):
        if showbuttontext:
            inner = SPAN(buttontext, _class='ui-button-text')
        else:
            inner = SPAN(XML('&nbsp'), _style='padding: 0px 7px 0px 6px;')
        return A(SPAN(_class='ui-icon ' + buttonclass),
                 inner,
                 _title=buttontext, _href=buttonurl, _class='ui-btn', **attr)
    """
    Vesion jstree3 con carga inicial de solo root nodes y los hijos con ajax/get_node
    """
    def get_node(self,nodeid):
        data=[]
        if  self._children:  # si no tiene hijos, ver si tiene asignaciones en la tabla maestra
            tabla = self._children[0].table
            fieldid = self._children[1]
            fieldname = self._children[0]
            fieldtipo=self._children[2]
            db = tabla._db
        if nodeid=='#':
            if self._idcontainer:
                id = self.tree_model.roots().select().first().id
                nodes = self.tree_model.get_childs_from_node(id).select() #plugin select no muestro raiz
            else:
                nodes = self.tree_model.roots().select() # plugin de mantenimiento muestro desde raiz
        else:
            id=nodeid
            if str(id).find('_')>=0:
                id=id.split("_")[1]
            nodes = self.tree_model.get_childs_from_node(id).select()
        for i, node in enumerate(nodes):
            count= self.tree_model.count_descendants_from_node(node)
            children=(count>0)
            if self._children: # si no tiene hijos, ver si tiene asignaciones en la tabla maestra
                count+=db(fieldtipo==node.id).count()
                children+=2
            visible = True
            if  self.filter:
                #if not self.tree_model.db(self.filter)(self.tree_model.db.mod_cfl_tip.mod_tipo==node.id).select():
                rows=self.tree_model.descendants_from_node(node.id,include_self=True)(self.filter).select(self.tree_model.settings.table_node.id)
                if not rows:
                    visible=False
                else:
                    count=len(rows)
                    if count==1 and rows[0].id==node.id: # si el unico obtenido es él mismo, no hay descencdencia valida
                            count=0
            if visible:
                tipo='root' if count and children in [1,3] else None
                if self.count_descendants and count:
                    countx = " (%s)" % count
                else:
                    countx=""
                data.append(dict(id='node_%s' % node.id, text=node.name + countx, children=(count>0), type=tipo))

        if self._children:
            nodes = db(fieldtipo == id).select(fieldid, fieldname)
            for i, node in enumerate(nodes):
                data.append(dict(id='item_%s' % node[fieldid.name], text=node[fieldname.name], children=False,type='file'))
        return data

    
    """
    Version jstree 3, con carga inicial de todo el arbol (no usa ajax para get_node)
    """
    def build_tree_objects3(self, initially_select):
        initially_open = []
        data = []
        
        for child in self.tree_model.descendants_from_node(initially_select, include_self=True
                                                           ).select(orderby=self.tree_model.desc):
            node_el_id = 'node_%s' % child.id
            if not self.tree_model.is_leaf_node(child):
                initially_open.append(node_el_id)
            
            if child.level == 0:
                data.append(dict(text=child.name,
                             id=node_el_id,
                             children=[],
                             ))
            elif child.level >= 1:
                _data = data[:]
                for depth in range(child.level):
                    _data = _data[-1]['children']
                    
                _data.append(dict(text=child.name,
                                 id=node_el_id,
                                 children=[],
                                 ))
        #devuelvo data[0] porque está con doble corchete (matriz dentro de matriz)
        return data[0], initially_open

    def build_tree_objects(self, initially_select):
        if self._version==3: return self.build_tree_objects3(initially_select)
        initially_open = []
        data = []
        
        for child in self.tree_model.descendants_from_node(initially_select, include_self=True
                                                           ).select(orderby=self.tree_model.desc):
            node_el_id = 'node_%s' % child.id
            if not self.tree_model.is_leaf_node(child):
                initially_open.append(node_el_id)
            
            if child.level == 0:
                data.append(dict(data=child.name,
                             attr=dict(id=node_el_id, rel=child.node_type),
                             children=[],
                             ))
            elif child.level >= 1:
                _data = data[:]
                for depth in range(child.level):
                    _data = _data[-1]['children']
                
                _data.append(dict(data=child.name,
                                 attr=dict(id=node_el_id, rel=child.node_type),
                                 children=[],
                                 ))
        return data, initially_open


    def render_tree_crud_buttons(self):
        T = current.T
        ui = dict(buttonadd='ui-icon-plusthick',
                  buttondelete='ui-icon-close',
                  buttonedit='ui-icon-pencil')
        return DIV(
            A('x', _class='close', _href='#', _onclick='jQuery(this).parent().hide();'),
            self.recordbutton('%(buttonadd)s' % ui, T('Add'), '#', False, _id='add_node_button'),
            self.recordbutton('%(buttonedit)s' % ui, T('Edit'), '#', False, _id='edit_node_button'),
            self.recordbutton('%(buttondelete)s' % ui, T('Delete'), '#', False, _id='delete_node_button'),
            _id='tree_crud_buttons', _style='display:none;position:absolute;',
            _class='tree_crud_button alert-message info',
        )
    def _callback(self,request, user_signature=True,
                  hmac_key=None,
                  onsuccess=None,  # def onsuccess(affected_node_ids): ...
                  ):
        def check_authorization():
            if not URL.verify(request, user_signature=user_signature, hmac_key=hmac_key):
                raise HTTP(403)
        action = request.args[-1]
        if action == 'getnode':
            vars = request.vars
            if not vars.id:
                raise HTTP(406)
            current.response.headers['Content-Type'] = gluon.contenttype.contenttype('.json')
            raise HTTP(200, XML(json.dumps(self.get_node(vars.id))), **current.response.headers)
        elif action == 'new':
            check_authorization()
            vars = request.post_vars
            if not vars.name:
                raise HTTP(406)
            elif vars.name == '---':
                raise HTTP(406)
            node_id = self.tree_model.insert_node(vars.target, name=vars.name)
            if onsuccess:
                onsuccess([])
            raise HTTP(200, str(node_id))

        elif action == 'edit':
            check_authorization()
            vars = request.post_vars
            if not vars.name or vars.name == '---':
                raise HTTP(406)
            node = self.tree_model.get_node(vars.id)
            if not node:
                raise HTTP(404)
            if node.name == vars.name:
                raise HTTP(406)
            i= vars.name.find('(')
            if i>0: #le quitamos la cantidad entre paréntesis si tiene
                vars.name=vars.name[:i-1]
            node.update_record(name=vars.name)
            if onsuccess:
                onsuccess([])
            raise HTTP(200, 'true')

        elif action == 'delete':
            check_authorization()
            vars = request.post_vars
            node = self.tree_model.get_node(vars.id)
            if not self.tree_model.is_leaf_node(node) or not node:
                raise HTTP(404)
            affected_node_ids = [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]

            self.tree_model.delete_node(node)
            if onsuccess:
                onsuccess(affected_node_ids)
            raise HTTP(200, 'true')

        elif action == 'move':
            check_authorization()
            vars = request.post_vars
            node = self.tree_model.get_node(vars.id)
            if self.tree_model.is_root_node(node):
                raise HTTP(406)
            affected_node_ids = [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]

            parent_node = self.tree_model.get_node(vars.parent)
            position = int(vars.position)

            target_child = self.tree_model.get_first_child(parent_node)
            if target_child:
                tmp = None
                end_flag = False
                for i in range(position):
                    tmp = self.tree_model.get_next_sibling(target_child)
                    if tmp is False:
                        self.tree_model.move_node(node, target_child, 'right')
                        end_flag = True
                    target_child = tmp
                if end_flag is False:
                    self.tree_model.move_node(node, target_child, 'left')
            else:
                self.tree_model.move_node(node, parent_node)

            affected_node_ids += [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]
            if onsuccess:
                onsuccess(list(set(affected_node_ids)))

            raise HTTP(200, 'true')

    def __call__(self,
                 args=[],
                 ):

        def url(**b):
            b['args'] = args + b.get('args', [])
            b['user_signature'] = self._user_signature
            b['hmac_key'] = self._hmac_key
            return URL(**b)

        root_nodes = self.tree_model.roots().select()
        data = []
        initially_open = []
        if self._version==1: #carga completa del arbol
            for i, root_node in enumerate(root_nodes):
                _data, _initially_open = self.build_tree_objects(root_node)
                data.append(_data)
                initially_open += _initially_open

        from gluon.utils import web2py_uuid
        element_id = web2py_uuid()
        from gluon.globals import Response
        from gluon.globals import Storage
        _response = Response()
        _response._view_environment = current.globalenv.copy()
        _response._view_environment.update(
            request=Storage(folder=os.path.join(os.path.dirname(os.path.dirname(self._request.folder)), APP)),
            response=_response,
        )
        return XML(_response.render('plugin_jstree/block%s.html' % (self._version if self._version!=1 else ''),
                                   dict(url=url, data=data,keyword=self._keyword,
                                        initially_open=initially_open,
                                        tree_crud_buttons=self.render_tree_crud_buttons(),
                                        element_id=element_id,search=self._search, idcomponent=self._idcomponent,
                                        urlcomponent=self._urlcomponent,div_id=self._idcontainer , edit=self._edit_option,
                                        can_select='item' if self._children else 'node', filterdata=self.filterdata,
                                        APP=APP)))
