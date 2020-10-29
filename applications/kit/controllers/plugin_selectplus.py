# -*- coding: utf-8 -*-
# intente algo como
def index(): return dict(message="hello from plugin_selectplus/selectplus.py")

@auth.requires_login()
def referenced_data():
    """ shows dialog with reference add/edit form
    the idea is taken from "data" function, just first argument is the id of calling select box
    """
    
    try:    references_options_list_id = request.args[0]
    except: return T("ERR: references_options_list_id lacking")

    try:    action = request.args[1]
    except: return  T("ERR: action lacking")
    
    try:    referenced_table= request.args[2]
    except: return T("ERR: referenced_table lacking")
    
    #esto es para que asigne bien con el juego de caracteres correcto el valor por defecto
    if 'def_field' in request.vars:
        try:
            db[referenced_table][request.vars.def_field].default=request.vars.def_name.decode('latin-1').encode('utf-8')
            del(request.vars.def_name)
            del(request.vars.def_field)
        except: pass
        finally: pass
    if action=="edit":
        try: referenced_record_id = int( request.args[3] )
        except: response.flash = T("ERR: referenced_record_id lacking"); return (response.flash)
        form = SQLFORM(db[referenced_table], referenced_record_id) # edit/update/change
    else:
        form = SQLFORM(db[referenced_table]) # new/create/add
    from plugin_selectplus import selectaddplus_close_dialog
    selectaddplus_close_dialog(response,request,form,db)

    return BEAUTIFY(form)
