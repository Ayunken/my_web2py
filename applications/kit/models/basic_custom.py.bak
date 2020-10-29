#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
import datetime
from gluon import current
T=current.T

def myFormValidation(form):
    tabla,r,s=form.table,form.vars,form.record
    dupmessage=T('Valor ya existente en la base de datos')
    def validate_duplicates(query,s=None):
        if s:
            query=(query) & (tabla.id!=s.id)
        query=db(query).select()
        if query:
            return True
    db=tabla._db
    tablename=tabla._tablename
    if tabla==db.mod_val:
        mod_atr_id=int(form.custom.inpval.atr or tabla.atr.default)
        #integridad referencial en listas de valores atributos piezas
        #if db(db.mod_mod_atr.valores.contains(db.
        if validate_duplicates((((tabla.name==r.name) | (tabla.valor==r.valor) )  & (tabla.atr==mod_atr_id)),s):
            form.errors.valor=dupmessage
    elif tabla==db.mod_cmp:
        mod_id=int(form.custom.inpval.mod or tabla.mod.default)
        if mod_id==r.cmp_mod and r.cmp_tipo==MOD_CMP_TIPO.modulo:
            form.errors.cmp_mod=T('Un módulo no puede ser componente de sí mismo')
        elif not r.cmp_mod and r.cmp_tipo==MOD_CMP_TIPO.modulo:
            form.errors.cmp_mod=T('Módulo no puede estar vacío')
        elif not r.cmp_pie and r.cmp_tipo==MOD_CMP_TIPO.pieza:
            form.errors.cmp_pie=T('Pieza no puede estar vacío')
        if r.cmp_tipo==MOD_CMP_TIPO.modulo:
            errfield='cmp_mod'
            if mod_es_descendiente(db, mod_id, r.cmp_mod):
                form.errors.cmp_mod=T('Módulo padre es componente descendiente del módulo componente introducido')
            elif mod_es_ancestro(db, r.cmp_mod, mod_id):
                form.errors.cmp_mod=T('Módulo componente introducido es contenedor del módulo padre')
        else:
            errfield='cmp_pie'
        if validate_duplicates((((tabla.cmp_pie!=None) | (tabla.cmp_mod!=None )) & (tabla.mod==mod_id) & (tabla.cmp_pie==r.cmp_pie)  & (tabla.cmp_mod==r.cmp_mod) & (tabla.cmp_tipo==r.cmp_tipo)),s):
            form.errors[errfield]=dupmessage
    elif tabla==db.mod_cfg_tip:
        if tabla == db.mod_cfg_tip:
            idpater = int(form.custom.inpval.cfg or tabla.cfg.default)
            if validate_duplicates((tabla.mod_tipo == r.mod_tipo) & (tabla.cfg == idpater), s):
                form.errors.mod_tipo = dupmessage
    elif tabla in (db.mod_mod_atr,db.mod_cfg_tip_atr):
        form.vars.tipo=db.mod_atr(form.vars.atr).tipo
        if r.tipo==MOD_ATR_TIPO.valores:
            if r.valores:
                if not (str(r.val_def) in r.valores):
                    form.errors.val_def=T('No está en rango de valores')
            else:
                form.errors.valores = T('Debe seleccionar algún valor')
        if tabla==db.mod_mod_atr:
            idpater = int(form.custom.inpval.mod or tabla.mod.default)
            if validate_duplicates((tabla.atr==r.atr)  & (tabla.mod==idpater),s):
                form.errors.atr=dupmessage
        if tabla == db.mod_cfg_tip_atr:
            idpater = int(form.custom.inpval.cfg_tip or tabla.cfg_tip.default)
            if validate_duplicates((tabla.atr == r.atr) & (tabla.cfg_tip == idpater), s):
                form.errors.atr = dupmessage


def myFormAccepted(form):
    return
    tabla=form.table
    db=form.table._db
    if tabla==db.mod_mod_atr:
        mod_id=form.custom.inpval.mod  or tabla.mod.default
        custom.recolectar_atributos_ascendientes(mod_id, db)
    elif tabla==db.mod_cmp:
        mod_id=form.custom.inpval.mod or tabla.mod.default
        custom.recolectar_atributos_modulo(mod_id, tabla)
    elif tabla==db.mod_cfg_mod:
        mod_cfg=form.custom.inpval.cfg or tabla.cfg.default
        custom.recolectar_atributos_modulo(mod_cfg, tabla)

def myFormDeleted(table,id):
    db=table._db
    if table==db.mod_mod_atr:
        mod_id=table[id].mod
        recolectar_atributos_ascendientes(mod_id, db, id_modatr_del=id)
    elif table==db.mod_cmp:
        mod_id=table[id].mod
        recolectar_atributos_modulo(mod_id, table, id_modcmp_del=id)
    elif table==db.mod_cfg_mod:
        mod_id=table[id].cfg
        recolectar_atributos_modulo(id, table, id_modcmp_del=id)


def myFormCreated(form):
    return myFormAccepted(form)

class GRAL(): #constantes globales propias
    #opciones predeterminadas para SQLFORM.grid
    """
    ESTAS VARIABLES GLOBALES SE MANTIENEN LOS CAMBIOS SI LAS MODIFICAS INCLUSO ENTRE PAGINAS DIFERENTES DE LA MISMA SESION!!!!
    """
    dateFmt='%d/%m/%Y'
    dateFmtSTD='%Y-%m-%d'
    timeFmt='%d/%m/%Y %H:%M:%S'
    timeFmtSTD='%Y-%m-%d %H:%M:%S'
    dateFormat=T(dateFmt)
    dateError=T('Must be DD/MM/YYYY!')
    currency_simbol='€'
    labelcompany='INVERCA'
    grid_defaults={'exportclasses': dict(xml=False,json=False,tsv=False,tsv_with_hidden_cols=False,csv_with_hidden_cols=False),
                   'maxtextlength': 200,
                   'showbuttontext': False,
                   'paginate': 20,
                   'links_in_grid': True,
                   'details': False,
                   'oncreate' : myFormCreated,
                   'onvalidation' : myFormValidation,
                    'ondelete': myFormDeleted,
                    'onupdate' : myFormAccepted,
                   'represent_none': '',

                  }
    #opciones predeterminadas añadidas para PDFS de SQLFORM.grid
    grid_adddefaults_pdf={'paginate': None,
                          'csv': False,
                          'details': False,
                          'links_in_grid': False
                          }
    grid_pdf_defaults=grid_defaults.copy()
    grid_pdf_defaults.update(grid_adddefaults_pdf)
    def represent_currency(self, value):
        if value == None:
            return DIV('-', _style='text-align: right;')
        else:
            return DIV('%.2f%s' % ((0 if value == None else value), self.currency_simbol), _style='text-align: right;')


    def fechaq(self,fecha):
        return datetime.date(fecha.year, fecha.month, fecha.day)
