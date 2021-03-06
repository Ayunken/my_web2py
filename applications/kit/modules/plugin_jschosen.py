#!/usr/bin/env python
# -*- coding: utf-8 -*-
#convierte un select options de lista desplegable en uno combiando con búsqueda
#
from gluon import *
from gluon.utils import web2py_uuid
import uuid
"""
    f: campo (db.table.field)
    v: Valor
    multi: True para activar multiselección
"""
def jschosen_widget_multiple(f,v):
    return jschosen_widget(f, v, multi=True)
def jschosen_widget(f,v,multi=False):
    T=current.T
    request=current.request
    #ãñadimos a las cabeceras los archivos de styles y javascript del pluging
    current.response.files.append(URL(r=request,c='static/plugin_jschosen',f='chosen.css'))
    current.response.files.append(URL(r=request,c='static/plugin_jschosen',f='chosen.jquery.min.js'))
    d_id = "jschosen-" + str(uuid.uuid4())[:8]
    wrapper = DIV(_id=d_id)
    inp = SQLFORM.widgets.options.widget(f,v)
    if multi:
        inp['_multiple'] = 'multiple'
    if v:
        if not isinstance(v,list):
            v = str(v).split('|')
        else:
            v=[str(i) for i in v]
        opts = inp.elements('option')
        for op in opts:
            if op['_value'] in v:
                op['_selected'] = 'selected'

    scr = SCRIPT('$(function() { $("#%s").chosen({\
                no_results_text: "%s", width: "100%%", \
                placeholder_text_single: "%s %s",\
                placeholder_text_multiple: "%s %s"\
                })});' % (inp['_id'],T("Sin resultados para"),T("Seleccione "),f.name,T("Seleccione varios"),f.name+'s'))
    wrapper.append(inp)
    wrapper.append(scr)
    if request.vars.get(inp['_id']+'[]',None):
        var = request.vars[inp['_id']+'[]']
        if not isinstance(var,list): var = [var]
        request.vars[f.name] = var
        del request.vars[inp['_id']+'[]']
    return wrapper
