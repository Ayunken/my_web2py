#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
import datetime
from gluon import current
from plugin_jstree import JsTree
import sys, re, os
import basic
from math import *
from gluon.storage import Storage
# import numpy as np

T = current.T

class IS_MY_LIST(IS_LIST_OF):
    #LISTA NUMERICA DE LO QUESEA
    def validate(self, value, record_id=None):
        value=[float(i) if int(i)!=float(i) else int(i) for i in value.strip('][').split(',')]
        return IS_LIST_OF.validate(self,value,record_id)
## validador
class IS_FORMULA(object):
    def __init__(self, db, field_variables, error_message=T('Fórmula incorrecta: '), current_atr_id=None, atrs={}):
        self.db = db
        self.field_variables = field_variables
        self.table = db[field_variables._tablename]
        self.e = error_message
        self.atr_id = current_atr_id
        self.atrs = atrs

    def _busca_atr_en_descendientes(self, atr_id, formula):
        lista = IS_FORMULA.lista_vars(formula)
        for i in lista:
            reg = self.table(i)
            if reg:
                if FORMULAS_PREFIJO[0] + str(atr_id) in reg.val_def_formula:
                    return True
                else:
                    if self._busca_atr_en_descendientes(atr_id, reg.val_def_formula):
                        return True

    def __call__(self, value):
        ret, error = self._validate(value)
        if error:
            # errores a ingnorar
            if not 'IndexError' in error:  # si hay un índice fuera de rango (en validación, se ignora)
                return (ret, self.e + error)
        return (ret, None)

    def _validate(self, value):
        errores = ''
        variables = {}
        formula = str(value).replace('%', '%%')  # por si se usa operador matematico % (como literal en un string..)
        lista = IS_FORMULA.lista_vars(formula)
        if self.atr_id:
            if self.table[self.atr_id].clave in lista:
                errores = T('Referencia cíclica al atributo actual ')
        if not errores:
            # convertir formula con nombres de atr en formulas con id de atr
            for key in lista:
                if key == 'n':
                    if not (
                            'sumv' in formula or 'sumd' in formula):  # n aceptado como nombre de variable dentro de funciones iterativas como sumv
                        errores += 'variable especial n solo admitida en funciones iterativas (sumv,sumd)'
                    else:
                        variables[key] = key
                else:
                    row = self.table(self.field_variables == key)
                    if row:
                        if self.atr_id and row.tipo != MOD_ATR_TIPO.valores:
                            if self._busca_atr_en_descendientes(self.atr_id, row.val_def_formula):
                                errores += '%satributo %s tiene referencias al atributo actual' % (
                                ',' if errores else '', key)
                        if row.id in self.atrs:
                            valor = self.atrs[row.id].value
                        else:
                            valor = row.id  # pongo el 1 para que tenga un valor
                            # if row.tipo==MOD_ATR_TIPO.valores and row.val_def:        #    ESTO LO QUTÉ PORQUE NO SÉ POR QUÉ PUSE VALOR, CUANDO AQUI
                            #    valor = self.db.mod_val(row.val_def).valor or valor   #    EL VALOR DE LA VARIABLE HA DE SER EL ID PARA CAMBIAR @ATR.NAME POR @ATR.ID y poder enviarselo a FORMULA PARA EVALUAR
                        variables[key] = valor
                        self.atrs[row.id] = InverAtr(valor, key=row.clave, name=row.name, tipo=row.tipo)
                        busca = '%s%s' % (FORMULAS_PREFIJO, key)
                        cambia = '%s%%(%s)s' % (FORMULAS_PREFIJO, key)
                        formula = formula.replace(busca, cambia)
                    else:
                        errores += '%satributo %s no existe' % (',' if errores else '', key)

        if not errores:
            formula = (formula % variables)
            self.formul = Formula(self.atrs)
            res = self.formul(formula)
            if self.formul.error:
                errores = self.formul.error
                if "TypeError" in errores or "KeyError" in errores or "AttributeError' in errores":
                    errores = None
        return formula if not errores else value, errores

    def formatter(self, value):
        return IS_FORMULA.formatea(self.db, value, self.field_variables)

    @staticmethod
    def lista_vars(cadena):
        lst = []
        if cadena:
            regex = re.compile(
                FORMULAS_REGEXPR)  # busca cadenas de texto que empiezen por { (no sigan por '{' ) y acaben en '}'
            lista = regex.findall(str(cadena))
            for k in range(0, len(lista)):
                if is_number(lista[k]):
                    lista[k] = int(lista[k])
                if not lista[k] in lst:
                    lst.append(lista[k])
            return lst
        else:
            return []

    @staticmethod
    def formatea(db, value, field_variables):
        table = db[field_variables._tablename]
        if value:
            lista = IS_FORMULA.lista_vars(value)
            formula = value
            for key in lista:
                row = table(key)
                if row:
                    name = row[field_variables.name]  # y o cambiamos por el nombre clave de la variable
                else:
                    name = key
                formula = formula.replace(FORMULAS_PREFIJO + str(key), FORMULAS_PREFIJO + name)
            return formula
        else:
            return ''

    @staticmethod
    def formatea_ro(db, value, field_variables):  # VISUALIZACION HTML de las formulas
        cad = IS_FORMULA.formatea(db, value, field_variables) + ' '
        for i in ['sumv', 'sumd']:  # funciones
            cad = cad.replace(i, '#%s$' % i)
        cad = cad.replace('k(', "!")
        if cad:
            c = ''
            ret = []
            kit = vari = False
            for i in cad:
                if i in ("#", '!', FORMULAS_PREFIJO):
                    if i == "!":
                        kit = True
                    if i == FORMULAS_PREFIJO:
                        vari = True
                    if c:
                        ret.append(SPAN(c))
                        c = ''
                elif i == ')' and kit:
                    if c:
                        c = db.mod(c).name
                        ret.append(SPAN('{%s..}' % c[0:7], _title=c,
                                        _style='background-color: pink; border: 1px solid blue; border-radius: 5px; padding: 1px; text-transform: lowercase; font-size: 10px;'))
                        c = ''
                        kit = False
                elif i == "$":
                    if c:
                        ret.append(SPAN(c, _style='color:blue; font-size: 12px;'))
                        c = ''
                else:
                    if vari:
                        if not i.upper() in "01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ_" and c:
                            r = db(db.mod_atr.clave == c).select().first()
                            ret.append(SPAN(c, _title=r.name if r else None,
                                            _style='background-color: cyan; border: 1px solid blue; border-radius: 5px; padding: 1px; text-transform: lowercase; font-size: 10px;'))
                            c = ''
                            vari = False
                    c += i

            if c:
                ret.append(SPAN(c))
            return DIV(ret)

class IS_RANGE(IS_FORMULA):
    def formatter(self, value):
        return IS_FORMULA.formatter(self, value)

    def __call__(self, value):
        (ret, e) = IS_FORMULA.__call__(self, 'xrange(%s)' % value)
        if not e:
            ret = ret.replace('xrange(', '')[0:-1]
        return ret, e

class Formula(object):
    """
    Evalúa una fórmula de un presupuesto buscando los valores de variables en atributos del diccionario
    uso: formula=Formula(db, {1:['V/F',valor]},'5*[1]')    # donde [1] es el atributo con id=1, que ha de estar en el diccionario de atributos
         formula._expresion         #devuelve la expresion ya con valores lista para evaluar, si se instanció el objeto pasando la formula, no la vuelve a calcular
         formula()                  #evalua la expresion ya calculada de la formula pasada al instanciar
         formula('5*[2]')           #evalua una nueva expresion pasada como argumento
         formula.expresion('5*[3]') #devuelve la expresion de la formula pasada como argumento
    """
    def __init__(self, atrdict, formula=None, default=1, extravars=None):
        # atrdict: diccionario de atributos
        #        {idatr: [tipo,valor],....}
        # formula a evaluar
        # default, valor a tomar si el atributo está en lista
        # Extrae la lista de variables que usa
        self.atrdict = atrdict  # list de InverAtr.
        # Rellena diccionario de variables con el su valor en el prespuestos

        self.var = {}  # dict de varibles por indice con su valor
        if formula:
            self._expresion = self.expresion(formula)
        else:
            self._expresion = None
        self.error = None
        self.default = default
        self.extravars = extravars or {}

    def lista_variables(self, formula):
        return IS_FORMULA.lista_vars(formula)

    def busca_funcion_parentesis(self, cadena, buscar, i):
        # busca en la cadena buscar y si le sigue una expresion entre parentesis y devuelve la posicion de inicio y de fin del parentesis cerrado
        ini = cadena.find(buscar, i)
        if ini >= 0:
            res = cadena[ini:]
            par = 0
            for k in range(ini, len(cadena)):
                j = cadena[k]
                if j == "(":
                    par += 1
                elif j == ")":
                    par -= 1
                    if par == 0:
                        return ini, k + 1
            return -1, -1
        else:
            return -1, -1

    def expresion(self, f):
        formula = f
        lista = self.lista_variables(formula)
        self.var = {}
        for key in lista:
            if key in self.atrdict:
                valor = self.atrdict[key].value or 0
                if self.atrdict[key].tipo == MOD_ATR_TIPO.vector:
                    if not isinstance(self.atrdict[key].value, list):
                        valor = [valor]
                elif self.atrdict[key].tipo == MOD_ATR_TIPO.diccionario:
                    if not isinstance(self.atrdict[key].value, dict):
                        valor = {0: valor}
            else:
                valor=0
            buscar = '%s%s' % (FORMULAS_PREFIJO, key)
            cambiar = 'var[%s]' % (key)
            formula = formula.replace(buscar, cambiar)
            self.var[key] = valNumOrStr(valor)

        # agregar comillas al uso de  funciones como sumv cuyo argumento es una expresion a evaluar
        # regex = re.compile('sum[vd]\([^\)]*\)')
        for fun in ('sumv', 'sumd'):
            emp = 0
            while True:
                i, k = self.busca_funcion_parentesis(formula, fun, emp)
                if k == -1: break
                cad = formula[i:k]
                cambio = cad
                if not '[v]' in cambio and not '[d]' in cambio:  # si ya ha usado [v] o [d] en en la expresión no los cambiamos
                    for key in lista:
                        if is_integer(key):
                            buscar = 'var[%s]' % key
                            if key in self.atrdict:
                                if (isinstance(self.atrdict[key].value, (list)) or
                                            self.atrdict[key].tipo == MOD_ATR_TIPO.vector) and fun == 'sumv':
                                    cambiar = 'var[%s][v]' % (key)
                                    cambio = cambio.replace(buscar, cambiar)
                                if (isinstance(self.atrdict[key].value, (dict)) or self.atrdict[
                                    key].tipo == MOD_ATR_TIPO.diccionario) and fun == 'sumd':
                                    cambiar = 'var[%s][d]' % (key)
                                    cambio = cambio.replace(buscar, cambiar)
                cambio = cambio.replace("(", "('", 1)[0:-1] + "')"
                # HAY QUE HACER OTRA FORMA DE REEMPLAZAR PORQUE SI LA MISMA CADENA ESTÁ MAS DE UNA VEZ PUEDE HABER PROBLEMAS POR EJEMPLO SI PONES DOS EXPRESIONES IGUALES USMADAS= SUMV(XX) +SUMV(XX)
                formula = formula.replace(cad, cambio)
                emp = k + 1
        return formula

    def __call__(self, formula=None):  # devuelve el resultado evaluado
        def sumv(formula):
            from functools import reduce
            # averiguo el nº de elementos de primera matriz que me encuentro. Todas las variables matriciales usadas en sumv deben tener el mismo nº de elementos
            ### ****** HAY QUE AVERIGUAR LA LONGITUD DEL VECTOR USADO EN LA SUMA, SEA UNA VARIABLE VECTOR UN ELEMENTO VECTOR DE UN DICCIONARIO
            #### HAY QUE ENCONTRAR LA LONGITUD DE LA ATRIBUTO VECTOR QUE SE SETÁ USANDO EN SUMV (EN VAR ESTAN TODAS LAS DE LA FORMULA)
            i = formula.find('var[')
            if i > -1:
                j = formula.find("]", i + 1)
                if j:
                    v = var.get(int(formula[i + 4:j]))
                    if isinstance(v, dict):
                        ii = formula.find(']', j + 1)
                        if ii > -1:
                            v = v.get(eval(formula[j + 2:ii]))
                    if isinstance(v, list):  # n devuelve indices de 0 a len(v)
                        r = reduce(lambda x, y: x + y, [eval(formula) for v in range(0, len(v))])
                        return r or 0
                    else:
                        return v

        def sumd(formula):
            from functools import reduce
            i = formula.find('var[')
            if i > -1:
                j = formula.find("]", i + 1)
                if j:  # busco una variables con valor dict para iterar n sus elemntos iterados mediante la clave en n. No debería haber más de una variable de dicionaro (y si hay más de una, deben tener las mismas claves)
                    v = var.get(int(formula[i + 4:j]))
                    if isinstance(v, dict) and v:
                        r = reduce(lambda x, y: x + y,
                                   [eval(formula) if not isinstance(k, list) else reduce(lambda x, y: x + y, k) for d, k
                                    in v.items()])
                        return r

        def k(id):
            return self.extravars.get(id)

        if formula:
            self._expresion = self.expresion(formula)
        var = self.var
        try:
            return eval(self._expresion)
        except:
            self.error = str(sys.exc_info()[0])
            return None

class Formula_Pre(Formula):
    """
    Evalúa una fórmula de un presupuesto buscando los valores de variables en atributos del presupuesto mod_pre_atr
    uso: formula=Formula(1,'5*[1]')    # donde [1] es el atributo con id=1
         formula._expresion         #devuelve la expresion ya con valores lista para evaluar, si se instanció el objeto pasando la formula, no la vuelve a calcular
         formula()                  #evalua la expresion ya calculada de la formula pasada al instanciar
         formula('5*[2]')           #evalua una nueva expresion pasada como argumento
         formula.expresion('5*[3]') #devuelve la expresion de la formula pasada como argumento
         ESTO CUANDO PUEDAS SIMPLIFICALO Y HAZLO EXTENDIENDO LA CLASE FORMULA
    """
    def __init__(self, db, id_pre, formula=None):
        self.id_pre = id_pre
        # Rellena diccionario de variables con el su valor en el presupuestos
        self.db = db
        Formula.__init__(self, self._carga_vars(db, self.id_pre, formula), formula)

    def _carga_vars(self, db, id_pre, formula):
        def addatr(row):
            if row:
                if row.atr.tipo == MOD_ATR_TIPO.valores:  # si tipo variable es valores, hay que buscar su valor en mod_val
                    valor = db.mod_val(row.valor).valor
                else:
                    valor = row.valor
                var[row.atr.id] = InverAtr(valor, row.atr.id, row.atr.name, row.atr.tipo)

        var = {}
        tabla = db.mod_pre_atr
        if formula:
            for key in self.lista_variables(formula):
                row = db((tabla.atr == key) & (tabla.pre == id_pre)).select(tabla.atr, tabla.valor).first()
                addatr(row)
        else:
            rows = db((tabla.pre == id_pre)).select(tabla.atr, tabla.valor)
            if rows:
                [addatr(row) for row in rows]
        return var

    def get_range_atr(self,
                      id_atr):  # devuelve LIST del rango desarrollado de un atributo tipo valores con rango, sustituyendo las variables del presupuesto si hay
        atr = self.db.mod_atr(id_atr)
        rango = [str(self(i)) for i in atr.rango.split(',')]
        lista = rango_decimal(','.join(rango))
        rango = [(float(i), '%s %s' % (i, atr.um.cod_SI)) for i in lista]
        return rango

class Formula_ModAtr(Formula):
    def __init__(self, id, table=None, fieldid='mod', formula=None, extravars=None):
        self.id = id
        # Rellena diccionario de variables con el valor en el modulo
        # Si en el init se indica formula, la lista de variables a usar se circunscribe a las usadas en la formula
        # No pasar formula en el init para reusar el objecto para calcular varias formulas del mismo  modulo y llamadas () posteriores
        self.db = db
        self.table = table or db.mod_mod_atr
        self.fieldid = self.table[fieldid]

        Formula.__init__(self, self._carga_vars(db, self.id, formula), formula, extravars=extravars)

    def _carga_vars(self, db, id, formula):
        def addatr(row):
            if row.tipo == MOD_ATR_TIPO.valores:  # si tipo variable es valores, hay que buscar su valor en mod_val
                valor = db.mod_val[row.val_def].valor
            elif row.tipo == MOD_ATR_TIPO.vector:  # si tipo variable es valores, hay que buscar su valor en mod_val
                valor = eval(row.val_def_formula) if row.val_def_formula else [0]
            elif row.tipo == MOD_ATR_TIPO.diccionario:  # si tipo variable es valores, hay que buscar su valor en mod_val
                valor = eval(row.val_def_formula) if row.val_def_formula else {}
            else:
                valor = row.val_def_formula if row.val_def_formula != None else 0
                valor = valNumOrStr(valor)
            id = row.get('atr') or row.id
            var[id] = InverAtr(valor, id, '', row.tipo)

        var = {}
        if formula:
            for key in self.lista_variables(formula):
                row = db((self.table.atr == key) & (self.fieldid == id)).select().first()
                if row:
                    addatr(row)
                else:
                    addatr(self.db.mod_atr(key))
        else:
            rows = db((self.fieldid == id)).select()
            if rows:
                [addatr(row) for row in rows]
        return var

    def get_range_atr(self,
                      id_atr):  # devuelve LIST del rango desarrollado de un atributo tipo valores con rango, sustituyendo las variables del presupuesto si hay
        atr = self.db.mod_atr(id_atr)
        rango = [str(self(i)) for i in atr.rango.split(',')]
        lista = rango_decimal(','.join(rango))
        return [(float(i), '%s %s' % (i, atr.um.cod_SI)) for i in lista]

class JsTree_cfgmod(JsTree):
    """
    version de JsTree para el arbol de tipos de módulos en ficha de Configuracion
    se reescribe la rutina get_node
    """
    def __init__(self, tree_model, cfg_id, **resto):
        JsTree.__init__(self, tree_model, **resto)

    def get_node(self, nodeid):
        data = []
        db = self.tree_model.table._db
        if nodeid == '#':
            nodes = self.tree_model.roots().select()  # plugin de mantenimiento muestro desde raiz
        else:
            id = nodeid
            if str(id).find('_') >= 0:
                id = id.split("_")[1]
            nodes = self.tree_model.get_childs_from_node(id).select()
        for i, node in enumerate(nodes):
            count = self.tree_model.count_descendants_from_node(node)
            visible = True
            if self.filter:
                # if not self.tree_model.db(self.filter)(self.tree_model.db.mod_cfl_tip.mod_tipo==node.id).select():
                self.filter = (self.filter) & (db.mod.tipo.contains(db.mod_cfg_tip.mod_tipo)) & (
                db.mod.id == db.mod_cfg_mod.mod)
                left = None  # db.mod_cfg_mod.on(db.mod_cfg_mod.tipo==db.mod_cfl_tip.mod_tipo)
                suma = db.mod_cfg_mod.id.count();
                field_id = self.tree_model.settings.table_node.id
                field2 = db.mod_cfl_tip.min_mods
                rows = self.tree_model.descendants_from_node(node.id, include_self=True)(self.filter).select(field_id,
                                                                                                             field2,
                                                                                                             suma,
                                                                                                             left=left,
                                                                                                             distinct=True,
                                                                                                             groupby=[
                                                                                                                 field_id,
                                                                                                                 field2])
                if not rows:
                    visible = False
                else:
                    count = len(rows)
                    children = (count > 0)
                    if count == 1 and rows[
                        0].mod_tipos.id == node.id:  # si el unico obtenido es él mismo, no hay descencdencia valida
                        count = rows[0].mod_cfl_tip.min_mods
                        children = False
                ################ CUSTOM CUSTOM CUSTOM ##############
                #### Contar numero de modulos que tienen la configuracion en este tipo de modulo
                count2 = 0
                for r in rows:
                    count2 += r[suma]
            if visible:
                tipo = 'root' if count  else None
                if count2 == count:
                    tipo = "ok"
                else:
                    tipo = "nok"
                countx = " [%s/%s]" % (count2, count)
                data.append(dict(id='node_%s' % node.id, text=node.name + countx, children=children, type=tipo))
        return data

    def __call__(self, args=[]):
        return JsTree.__call__(self, args=[])

def rango_decimal(rango):
    """ desarrolla un rango con intervalo float """
    def multiplica_Rango(l, f):
        r = []
        for i in l:
            r += [int(float(i) * f)]
        return r

    def divide_Rango(l, f):
        r = []
        for i in l:
            r += [float(i) / f]
        return r

    l = rango.split(',')
    try:
        for i in l:
            if not is_integer(i):  # encuentro algun decimal, así que lo desarrollamos con dcimales
                l = multiplica_Rango(l, 1000)
                l = range(*l)
                l = divide_Rango(l, 1000)
                return l
        l = multiplica_Rango(l, 1)  # solo es par pasarlo a entero
        return range(*l)
    except:
        return []

def recolectar_atributos_modulo(id, t_cmp, id_modcmp_del=None, id_modatr_del=None):
    return  # DESACTIVADO!!!

    """
        combina los atributos de los componentes de un modulo o configuracion para rehacer la lista de atributos del modulo padre o configuracion
        id_deleted=id de un mod_mod_atr que se va a eliminar, para obviarlo y no incluirlo
    """

    db = t_cmp._db
    t_atr_mod = db.mod_mod_atr  # atributos de modulos son los que se buscan y combinan (NUNCA LOS DE CONFIG.)
    if t_cmp == db.mod_cfg_mod:  # componentes de configiuracion
        field_id_padre = 'cfg'
        field_id_cmp = 'mod'
        """id_cfl=db.mod_cfg(id)
        if id_cfl:
            id_cfl.cfl_base #esto está filtrado porque daba algún error al actualizar modulos, pero no está revisado qué pasa si esto sigue con id_cfl nulo
        """
    else:  # componenes de moodulo
        field_id_padre = 'mod'
        field_id_cmp = 'cmp_mod'
        t_atr = t_atr_mod

    def combina_atributos(atr1, atr2):
        if atr1['atr'] == atr2['atr']:
            if atr1['tipo'] == MOD_ATR_TIPO.valores:
                atr1['valores'] += (x for x in atr2['valores'] if not x in atr1['valores'])
                # print '%s %s r:%s' % (atr1['valores'],atr2['valores'],atr['valores'])
                if not atr1['val_def'] in atr1['valores']:
                    atr1['val_def'] = atr2['val_def']
                elif len(atr1['valores']) > 0:
                    atr1['val_def'] = atr1['valores'][0]
            else:
                # atr['rango']  POR AHORA LOS DEJO TAL CUAL EL PRIMERO, PERO HABRA QUE HALLAR UN ALGORITMO QUE PERMITA COMBINAR RANGOS EN MODO ABREVIADO
                # atr['val_def_formula']
                pass
            return atr1

    atributos = []
    atributos_data = {}
    # atributos de módulos componentes
    fields = [t_atr_mod.atr, t_atr_mod.tipo, t_atr_mod.valores, t_atr_mod.val_def, t_atr_mod.rango,
              t_atr_mod.val_def_formula]
    rows = db((t_cmp[field_id_padre] == id) & (t_cmp.id != id_modcmp_del) & (t_atr_mod.id != id_modatr_del)).select(
        *fields, join=t_atr_mod.on(t_atr_mod.mod == t_cmp[field_id_cmp]))
    if rows:
        for x in rows:
            v = x['atr']
            if v:
                if int(v) in atributos:
                    atributos_data[v] = combina_atributos(atributos_data[v], x.as_dict())
                else:
                    atributos.append(int(v))
                    atributos_data[v] = x.as_dict()

    if t_cmp == db.mod_cfg_mod:  # componentes de configuracion base
        # atributos provinientes de la plantilla de configuracion base
        fields = [db.mod_cfl_atr.atr, db.mod_cfl_atr.tipo, db.mod_cfl_atr.valores, db.mod_cfl_atr.val_def,
                  db.mod_cfl_atr.rango,
                  db.mod_cfl_atr.val_def_formula]
        rows = db(db.mod_cfl_atr.cfl == id_cfl).select(*fields)
        if rows:
            for x in rows:
                v = x['atr']
                if v:
                    if int(v) in atributos:
                        atributos_data[v] = combina_atributos(atributos_data[v], x.as_dict())
                    else:
                        atributos.append(int(v))
                        atributos_data[v] = x.as_dict()

    # atributos usados en fórmulas de componentes
    rows = db(t_cmp[field_id_padre] == id).select(t_cmp.formula)
    if rows:
        for r in rows:
            lista = IS_FORMULA.lista_vars(r['formula'])
            if lista:
                for v in lista:
                    if not int(v) in atributos:
                        atributos.append(int(v))
    # GUARDAR ATRIBUTOS
    db((t_atr[field_id_padre] == id) & (t_atr.lock == False)).update(lock=None)
    if atributos:
        for ida in atributos:
            if not ida in atributos_data:
                atr = db.mod_atr(ida)
                atributos_data[ida] = dict(tipo=atr.tipo, atr=atr.id, val_def=atr.val_def,
                                           val_def_formula=atr.val_def_formula, rango=atr.rango)
                if atr.tipo == MOD_ATR_TIPO.valores:
                    v = db.mod_val(db.mod_val.atr == ida)
                    if hasattr(v, 'select'):
                        v = v.select(fields=db.mod_val.id)
                        atributos_data[ida]['valores'] = (', '.join(i['id'] for i in v))
                        if not atributos_data[ida]['val_def']:
                            atributos_data[ida]['val_def'] = atributos_data[ida]['valores'][0]
            atributos_data[ida]['lock'] = False
            for i in ['id', 'rango', 'val_def']:
                if i in atributos_data[ida]: del atributos_data[ida][i]
            atributos_data[ida][field_id_padre] = id
            modatr = db((t_atr.atr == ida) & (t_atr[field_id_padre] == id)).select().first()
            t_atr.update_or_insert((t_atr.atr == ida) & (t_atr[field_id_padre] == id), **atributos_data[ida])
            # if modatr:
            #    modatr.update_or_insert(**atributos_data[ida])
            # else:
            #    t_atr.insert(**atributos_data[ida])
    # finalmente eliminamos los existentes no manuales que no se han tocado
    s = db((t_atr[field_id_padre] == id) & (t_atr.lock == None))
    if s.select():
        s.delete()
    if t_cmp == db.mod_cmp:  # si son componentes de módulo, se repercute hacia los contenederos de este módulo. Si son componentes de cfg, no hace falta
        recolectar_atributos_ascendientes(id, db)

def recolectar_atributos_ascendientes(id, db, id_modcmp_del=None, id_modatr_del=None):
    t_cmp = db.mod_cmp
    for reg in db(db.mod_cmp.cmp_mod == id).select(db.mod_cmp.mod):
        recolectar_atributos_modulo(reg.mod, t_cmp, id_modcmp_del=id_modcmp_del, id_modatr_del=id_modatr_del)
    for reg in db(db.mod_cfg_mod.mod == id).select(db.mod_cfg_mod.cfg):
        recolectar_atributos_modulo(reg.cfg, db.mod_cfg_mod, id_modcmp_del=id_modcmp_del, id_modatr_del=id_modatr_del)

def mod_es_ancestro(db, mod_id, mod_padre):
    # Busca recursivamente si mod_id es ancestro de mod_padre
    rows = db((db.mod_cmp.cmp_mod == mod_padre) & (db.mod_cmp.cmp_tipo == MOD_CMP_TIPO.modulo)).select(db.mod_cmp.mod)
    if rows:
        for r in rows:
            if r.mod == mod_id:
                return True
            else:
                if mod_es_ancestro(db, mod_id, r.mod):
                    return True

def mod_es_descendiente(db, mod_id, mod_hijo):
    # Busca recursivamente si mod_id es descendiente de mod_hijo
    rows = db((db.mod_cmp.mod == mod_hijo) & (db.mod_cmp.cmp_tipo == MOD_CMP_TIPO.modulo)).select(db.mod_cmp.cmp_mod)
    if rows:
        for r in rows:
            if r.cmp_mod == mod_id:
                return True
            else:
                if mod_es_descendiente(db, mod_id, r.cmp_mod):
                    return True

def monta_descripcion_modulo(db, reg_or_id):
    from gluon.dal import Row
    if isinstance(reg_or_id, Row):
        reg = reg_or_id
    else:
        reg = db.mod[reg_or_id]
    campos = [db.mod_mod_atr.valores, db.mod_atr.abreviatura]
    # & (db.mod_mod_atr.lock==True)   # añadir lock si solo se quieren los atributos manuales y no los heredados
    rows = db((db.mod_mod_atr.mod == reg['id'])).select(*campos,
                                                        left=db.mod_atr.on(db.mod_mod_atr.atr == db.mod_atr.id),
                                                        orderby=~db.mod_atr.orden_descripcion)
    des = '' if reg['name_fix'] else db.mod_tipos[reg['tipo']].abreviatura + ' '
    if rows:
        for r in rows:
            if r.mod_mod_atr.valores:
                if len(r.mod_mod_atr.valores) == 1:
                    vreg = db.mod_val(r.mod_mod_atr.valores[0])
                    des += r.mod_atr.abreviatura % (vreg.abreviatura or vreg.name) + ' '
    if reg['name_fix']:
        if '%s' in reg['name_fix']:
            des = reg['name_fix'] % (des)
        else:
            des = reg['name_fix']
    return des.strip(' ')

def recolectar_atributos_presupuesto2(db,id_pre,atr,cfg,subnave=0):
    #recolecta atributos propios de subconfiguración concreta para un grupo de naves
    tabla=db.mod_cfg_tip_atr
    #db((db.mod_pre_atr.pre == id_pre)&(db.mod_pre_atr.subnave==subnave)).update(tag=False)
    rows = db((db.mod_cfg_tip_atr_combi.cfg == cfg) &(db.mod_atr.id==tabla.atr) & (tabla.id == db.mod_cfg_tip_atr_combi.cfg_tip_atr) & ((db.mod_cfg_tip.id==db.mod_cfg_tip_atr_combi.cfg_tip_ori))
              & ((db.mod_cfg_tip.cfg == cfg) ) & (db.mod_val.id==tabla.val_def) ).select(tabla.ALL,db.mod_cfg_tip.ALL,db.mod_atr.ALL,db.mod_val.ALL)  # los atributos originales o generales heredados
    if rows: #hay que filtrar los propios si así propios es pasado as true
        for row in rows:
            if row.mod_atr.id:
                if row.mod_atr.tipo==MOD_ATR_TIPO.valores:
                    idvalor=row[tabla.val_def]
                    valor=row.mod_val.valor
                else:
                    valor=row[tabla.val_def]
                    idvalor=None
                atr.add(valor, subnave, row.mod_cfg_tip.mod_tipo,idvalue=idvalor, **row.mod_atr)
            #TODO ESTA IGNORADO QUE SE DEN DE ALTA EN BD los atributos especificos de subtunel/modtipo TODAVIA NO SE SI SON NECESARIOS EN TABLA
            """db.mod_pre_atr.update_or_insert((db.mod_pre_atr.pre == id_pre) & (db.mod_pre_atr.cfg==cfg) & (db.mod_pre_atr.subnave==subnave)
                                            & (db.mod_pre_atr.mod_tipo == row.mod_cfg_tip.mod_tipo) & (db.mod_pre_atr.atr == row[tabla.atr]),
                                            pre=id_pre, cfg=cfg, subnave=subnave,atr=row[tabla.atr], mod_tipo=row.mod_cfg_tip.mod_tipo,
                                            valor=row[tabla.val_def] or row[tabla.val_def_formula],
                                            valores=row[tabla.valores],
                                            rango= row[tabla.rango],
                                            tipo=row[tabla.tipo],
                                            opcional=True if len(row[tabla.valores])>1 or row[tabla.rango] else False,
                                            tag=True)
    db((db.mod_pre_atr.pre == id_pre)&(db.mod_pre_atr.subnave==subnave) & (db.mod_pre_atr.tag == False)).delete()
    """

def recolectar_atributos_presupuesto(db,id_pre,cfg=None,subnave=0,inicial=True):
    """
      recolectar_atributos_presupuesto
      subnave=0 # Por defecto todas las variables les pone subnave=0 o variables por defecto
      incial boolean = si True las regenera todas, si false, solo las de grupo secundario (que son las que se basan en otras formulas->TODO MEJORA)
    """
    # TODO Incial=False debería recalcular los atributos que tienen fórmulas basadas en otros atributos, no solo las de grupo secundario, así no habría que tener cuidado de declararlas de grupo secundario
    if not cfg:
        cfg = db.mod_pre(id_pre).cfg
    tabla=db.mod_cfg_tip_atr_combi
    if inicial:
        db((db.mod_pre_atr.pre == id_pre)).update(tag=False)
        #SI SE TOMAN LOS DE LA CFG (50) Y SU PADRE (11) SALEN MÁS, PERO AUN FALTAN LOS DE VARIO VALORES!!!!
        rows = db((tabla.cfg== cfg) & ((db.mod_cfg_tip.id==tabla.cfg_tip))
                  & ((tabla.mod_tipo == tabla.mod_tipo_ori))
                  & (db.mod_atr.id==tabla.atr) ).select(tabla.ALL,db.mod_cfg_tip.cfg,db.mod_atr.grp_atr)  # los atributos originales o generales heredados
    else:#si no es inicial, siempre recalculamos los secundarios, porque se basan en primarios
        rows=db((tabla.cfg == cfg) &  (db.mod_cfg_tip.id==tabla.cfg_tip) & ((tabla.mod_tipo == tabla.mod_tipo_ori)) & (db.mod_atr.id==tabla.atr) & (db.mod_atr.grp_atr==ATR_ESPECIAL.GRUPO_SECUNDARIO)).select(tabla.ALL,db.mod_cfg_tip.cfg,db.mod_atr.grp_atr)  # los atributos originales o generales heredados

    if rows: #hay que filtrar los propios si así propios es pasado as true
        for row in rows:
            reg=db((db.mod_pre_atr.pre == id_pre) &  (db.mod_pre_atr.subnave==subnave)
                                            & (db.mod_pre_atr.mod_tipo == row[tabla.mod_tipo]) & (db.mod_pre_atr.atr == row[tabla.atr])).select().first()
            upd=dict(pre=id_pre, subnave=subnave,atr=row[tabla.atr], mod_tipo=row[tabla.mod_tipo],
                                            valor=row[tabla.val_def] or row[tabla.val_def_formula],
                                            valores=row[tabla.valores],
                                            rango= row[tabla.rango],
                                            tipo=row[tabla.tipo],
                                            opcional=True if len(row[tabla.valores])>1 or (row[tabla.rango] and row[tabla.tipo]==MOD_ATR_TIPO.formula) or row.mod_atr.grp_atr==ATR_ESPECIAL.GRUPO_SALIDA else False,
                                            tag=True)
            if reg:
                if inicial:
                    if upd['tipo']==MOD_ATR_TIPO.valores:
                        if int(reg.valor) in upd['valores']:
                            upd['valor']=reg.valor
                         #TODO Habria que ver también de Mantener un valor previo de tipo formula, aunque ello implica calcular el upd['rango'] para ver si está en la lista
                    reg.update_record(**upd)
                else:
                    if not reg.valor:
                        reg.update_record(valor=upd['valor'])
                        #pass
            else:
                db.mod_pre_atr.insert(**upd)

    if inicial:
        db((db.mod_pre_atr.pre == id_pre) & (db.mod_pre_atr.tag == False)).delete()

def recolecta_atributos_cfg(db,id_pre,subnave,cfg):
    tabla = db.mod_cfg_tip_atr_combi
    db(db.mod_pre_atr.pre == id_pre).update(tag=False)
    rows = db((tabla.cfg == id_cfg) & ((tabla.cfg_tip_ori == tabla.cfg_tip) | (
    tabla.mod_tipo == IDRAIZ_MOD_TIPO))).select()  # los atributos originales o generales heredados
    if rows:
        for row in rows:
            db.mod_pre_atr.update_or_insert(
                (db.mod_pre_atr.pre == id_pre) & (db.mod_pre_atr.cfg == id_cfg) & (db.mod_pre_atr.subnave == subnave)
                & (db.mod_pre_atr.mod_tipo == row.mod_tipo) & (db.mod_pre_atr.atr == row.atr),
                pre=id_pre, cfg=id_cfg, subnave=subnave, atr=row.atr, mod_tipo=row.mod_tipo,
                valor=row.val_def or row.val_def_formula,
                valores=row.valores,
                rango=row.rango,
                tipo=row.tipo,
                opcional=True if len(row.valores) > 1 or row.rango else False,
                tag=True)
    db((db.mod_pre_atr.pre == id_pre) & (db.mod_pre_atr.tag == False)).delete()

def field_sort_widget(field, value, row, orden='', **kwargs):
    wg = SQLFORM.widgets.string.widget(field, value, **kwargs)
    fh = 'inc-%s_row_%s' % (field.name, row['id'])
    js = '$("[name=%(fh)s]").val("%(signo)s"); $("form").submit();'
    wg = SPAN([wg, A(_class='input-group-addon icon glyphicon glyphicon-arrow-up',
                     _onclick=js % dict(fh=fh, signo=('-' if orden != '~' else '+'))),
               A(_class='input-group-addon icon glyphicon glyphicon-arrow-down',
                 _onclick=js % dict(fh=fh, signo=('+' if orden != '~' else '-'))),
               INPUT(_type='hidden', _name=fh, _value='')],
              _class='input-group')
    return wg

def options_widget_mod(field, value, row, **kwargs):
    from gluon.sqlhtml import OptionsWidget
    db = field.db
    cadena = None
    if field is db.mod_pre_atr.valor:
        if row.atr.tipo==MOD_ATR_TIPO.formula:
            value = str(float(Formula_Pre(db, db.mod_pre_atr(row['id']).pre, value)()))
        field.requires = None
        cadena = options_mod_pre_atr(db, row['id'])
        if cadena:
            if cadena==True and row.atr.grp_atr!=ATR_ESPECIAL.GRUPO_SALIDA:
                if field.requires:
                    value=field.requires.formatter(value)
                return SQLFORM.widgets.decimal.widget(field, value, **kwargs)
            else:
                del kwargs['_name']
                return LABEL( cadena if cadena!=True else value, **kwargs) #una sola opcion, no select
        else:
            return OptionsWidget.widget(field, value, **kwargs)

def options_mod_pre_atr(db, idreg):
    reg = db.mod_pre_atr[idreg]
    if reg:
        idcfg = db.mod_pre(reg.pre).cfg
        if reg.valores or reg.rango:
            um = reg.atr.um
            um = um.cod_SI if um else ''
            if reg.atr.tipo == MOD_ATR_TIPO.valores:
                #db.mod_pre_atr.valor.requires = IS_IN_DB(db(db.mod_val.id.belongs(atr_cfg.valores)), db.mod_val.id,'%(name)s %(atr)s', orderby=db.mod_val.name,zero=None)
                rows = db(db.mod_val.id.belongs(reg.valores)).select(db.mod_val.id, db.mod_val.name)
                lista = [(i.id, ('%(name)s ' % i) + um) for i in rows]
                if len(lista)==1:
                    return lista[0][1]
                else:
                    db.mod_pre_atr.valor.requires = IS_IN_SET(lista, zero=None)
            else: #calculo rango discreto de variable numero real
                valores = []
                for i in reg.rango.split(','):
                    res = Formula_Pre(db, reg.pre,
                                      i)()  # al pasarle la formula en la construccion, solo carga los atr del presup que van en la formula
                    valores += [str(res)]
                if len(valores)<=2: #rango real:
                    if len(valores)==1:
                        min=0
                        max=valores[0]
                    else:
                        min=valores[0]
                        max = valores[1]
                    db.mod_pre_atr.valor.requires = IS_DECIMAL_IN_RANGE(min,max,dot=',')
                    return True
                else:
                    lista = rango_decimal(','.join(valores))
                    lista = [(float(i), '%s %s' % (i, um)) for i in lista]
                    if len(lista) == 1: #mono valor, le asigno el único
                        return lista[0][1]
                    else:
                        db.mod_pre_atr.valor.requires = IS_IN_SET(lista)
        else:
            return True  # no hay options, habra que usar string

def int_or_float(number):
    #Devuelve int or float. si hay problemas, devuelve el mismo
    try:
        flotante = float(number)
        entero=int(flotante)
        return entero if flotante==entero else flotante
    except:
        return number
def modrul_lanza(db, idrul):
    def add_or_update_cmp(mod, tipo,cmp_pie,cmp_mod, cantidad,formula):
        if formula != None:
            setr=(db.mod_cmp.cmp_tipo == tipo) & (db.mod_cmp.mod == mod)
            if tipo==MOD_CMP_TIPO.modulo:
                setr = (setr & (db.mod_cmp.cmp_mod == cmp_mod))
            else:
                setr = (setr & (db.mod_cmp.cmp_pie == cmp_pie))
            row = db(setr).select().first()
            if row:
                if formula[0] in '-+/*':
                    valor = 'float(' + row.formula + ') ' + formula[0]+ ' '+str(cantidad)
                else:
                    valor = cantidad
                try:
                    valor = eval(valor)
                except:
                    pass
                if str(valor) == '0' or str(valor) == '0.0':
                    setr.delete()
                else:
                    row.update_record(formula=int_or_float(valor))
            else:
                try:
                    valor = eval(cantidad)
                except:
                    valor = cantidad
                if str(valor) != '0' and str(valor) != '0.0':
                    db.mod_cmp.insert(mod=mod, cmp_pie=cmp_pie,cmp_mod=cmp_mod, cmp_tipo=tipo, formula=int_or_float(valor))

    rul = db.mod_rul(idrul)
    if not rul:
        return 'regla %s no existe' % idrul

    rules=db(db.mod_rul_lin.mod_rul == idrul).select(orderby=db.mod_rul_lin.orden)
    mods=db(db.mod.name.like(rul.filtro_descripcion)).select(db.mod.id)
    veces=0
    for rul in rules:
        haydestino=(rul.tipo_tar != MOD_CMP_TIPO.ninguno and (rul.cmp_pie_tar or rul.cmp_mod_tar))
        for mod in mods:
            if rul.tipo_trg==MOD_CMP_TIPO.ninguno and haydestino:
                add_or_update_cmp(mod.id, rul.tipo_tar, rul.cmp_pie_tar,rul.cmp_mod_tar, rul.formula_tar, rul.formula_tar)  # sumo a target
                veces += 1
            else:
                r = db((db.mod_cmp.mod == mod.id) & (
    (db.mod_cmp.cmp_pie == rul.cmp_pie_trg) | (db.mod_cmp.cmp_mod == rul.cmp_mod_trg)) & (
                         db.mod_cmp.cmp_tipo == rul.tipo_trg) ).select().first()
                if r:
                    valororigen = r.formula
                    atrdict ={ATR_ESPECIAL.PZORIGEN:InverAtr(valororigen,id=ATR_ESPECIAL.PZORIGEN,tipo=MOD_ATR_TIPO.formula)}
                    expresion = rul.formula_tar
                    formula = Formula(atrdict, expresion)  # cargo calulo formula con atributos
                    cantidad = formula()
                    if haydestino:
                        veces+=1
                        add_or_update_cmp(mod.id, rul.tipo_tar, rul.cmp_pie_tar, rul.cmp_mod_tar, cantidad, rul.formula_tar)  # sumo a target
                    # modifico pieza origen
                    if rul.formula_trg != None :
                        cantidad2 = formula(rul.formula_trg)
                        if cantidad2!=cantidad:
                            add_or_update_cmp(mod.id,rul.tipo_trg, rul.cmp_pie_trg,rul.cmp_mod_trg, cantidad2,rul.formula_trg)  # afecto a orgien

    return 'Filtro aplicado correctamente %s mods'%veces

def report_fields_list(db):
    """ Lista de campos de cada informe """
    return {'mod_atr': [db.mod_atr.id, db.mod_atr.name, db.mod_atr.clave, db.mod_atr.grp_atr,
                        db.mod_atr.tipo,   db.mod_atr.um, db.mod_atr.rango,db.mod_atr.val_def
                       ]
            }

"""
def BORRAR_get_atr_cfg(cfg, atr):
    ## devuelve el valor del atributo atr en la configuracion cfg
    r = db((db.mod_cfg_atr.cfg == cfg) & (db.mod_cfg_atr.atr == atr)).select(db.mod_cfg_atr.val_def).first()
    if r:
        return r.val_def
        # TAMBIEN HABIRA QUE RECARGAR EL COMBO LIST DE ANCHOS...

def premod_genera_kits_OLD(db, pre):
    #Generación de los kits de un presupuesto
    #1-Recopilar todos los kits de las configuraciones usadas en mod_pre_naves. En principio no debería haber kits coincidentes con fórmula diferente, ha de salir distinctrow mod.id, mod_cfg_mod.formula
    #2-Calcular todas las fórmulas suministrandole los atributos del presupuesto
    #3-Calcular las piezas por desarrollo recurivo de los kits
    kits = premod_filtra_kits(db, pre)
    # kits=db(query).select(db.mod_cfg_mod.mod,db.mod_cfg_mod.formula,distinct=True)
    db(db.mod_pre_mod.pre == pre).update(cantidad=None)
    if kits:
        inver = Invernadero(db, pre)()
        formul = Formula(inver.atr)
        for kit in kits:
            res = formul(kit['formula'])
            db.mod_pre_mod.update_or_insert((db.mod_pre_mod.pre == pre) & (db.mod_pre_mod.mod == kit['mod']) & (
            db.mod_pre_mod.mod_tipo == kit['mod_tipo']), pre=pre, mod=kit['mod'], mod_tipo=kit['mod_tipo'],
                                            cantidad=res)
    db((db.mod_pre_mod.pre == pre) & (db.mod_pre_mod.cantidad == None)).delete()

def cfgmod_genera_kits_old2(db, idcfg=None, idcfgtip=None, update=True):
    tcfg = db.mod_cfg  # config maestro
    ttip = db.mod_cfg_tip  # tipos de modulos
    ttatr = db.mod_cfg_tip_atr
    # filtro módulos de tipo ubicacion definidos en la plantilla de la config.
    query = ((db.mod.tipo.contains(ttip.mod_tipo)) & (ttip.mod_tipo == db.mod_tipos.id))  # seleccion kits del tipo
    if idcfg:
        query = query & (ttip.cfg == idcfg)
    else:
        idcfg = ttip(idcfgtip).cfg
        query = query & (ttip.id == idcfgtip)
    # hasta aqui query ha seleccionado los tipos de la configuracion y los mod_tipos correspondientes
    kits = db(query).select(db.mod.id, ttip.id, ttip.mod_tipo, ttip.formula, distinct=True,
                            orderby=[ttip.mod_tipo])  # rows con todos los kits base que los tipos devuelven
    # CREO QUE HAY QUE IR RECORIENNDO KITS Rows y por cada uno buscar los atributos de cada tipo y sus ancestros y comparar. TAL VEZ SEA MAS SENCILLO AUNQUE NO CREO QUE MAS RAPIDO
    dentro = 0
    for row in kits:
        # selecciono los atributos de los ancestros del tipo actual
        qatrs = (ttatr.cfg_tip == ttip.id) & (ttip.mod_tipo == db.mod_tipos.id) & (ttip.cfg == idcfg)
        qatrs = qatrs & (db.mod_mod_atr.mod == row.mod.id) & (db.mod_atr.id == ttatr.atr) & (
        ttatr.atr == db.mod_mod_atr.atr) & ((ttatr.lock == True) | (ttatr.cfg_tip == row[ttip.id]))
        atrs = mptt.ancestors_from_node(row[ttip.mod_tipo], include_self=True)(qatrs)
        atrs = atrs.select(ttatr.atr, ttatr.valores, db.mod_mod_atr.valores, db.mod_atr.tipo, ttip.mod_tipo,
                           db.mod_tipos.level, distinct=True, orderby=(ttatr.atr, db.mod_tipos.level))
        batr = None

        def cumple(r):
            if r[ttatr.atr] and r.mod_atr.tipo == MOD_ATR_TIPO.valores and r.mod_mod_atr.valores and r[
                ttatr.valores]:  # si hay coincidencia de atributos en tip_cfg y en modulo, proceso a ver si tienen valores comunes
                if [item for item in r.mod_mod_atr.valores if item in r[ttatr.valores]]:
                    return True
                else:
                    return False

        # recorro los atributos y el último valor de cada atributo lo proceso, ya que es el del ultimo nivel
        if atrs:
            excluye = False
            for atr in atrs:
                if batr and batr[ttatr.atr] != atr[ttatr.atr]:
                    if not cumple(batr):
                        excluye = True
                        break
                batr = atr
            if excluye or not cumple(batr):
                row.mod.id = None
            else:
                dentro += 1

    if update:
        if idcfgtip:
            t = ttip(idcfgtip)
            idcfg = t.cfg
            query = ((db.mod_cfg_mod.mod_tipo == t.mod_tipo) & (db.mod_cfg_mod.cfg == idcfg))
        else:
            query = (db.mod_cfg_mod.cfg == idcfg)
        db(query).update(
            formula='-1')  # marco todos los componentes de la configuracion para luego borrr los no tocados
        for r in kits:
            if r.mod.id:
                db.mod_cfg_mod.update_or_insert((db.mod_cfg_mod.cfg == idcfg) & (db.mod_cfg_mod.mod == r[db.mod.id]) & (
                db.mod_cfg_mod.mod_tipo == r[ttip.mod_tipo]), cfg=idcfg, mod=r[db.mod.id], formula=r[ttip.formula],
                                                mod_tipo=r[ttip.mod_tipo])
        db(query & (db.mod_cfg_mod.formula == '-1')).delete()  # borro los que no han sido tocados
    return kits

def cfgmod_genera_kits_OLD(db, idcfg=None, idcfgtip=None, update=True):
    tcfg = db.mod_cfg  # config maestro
    ttip = db.mod_cfg_tip  # tipos de modulos
    ttatr = db.mod_cfg_tip_atr
    # filtro módulos de tipo ubicacion definidos en la plantilla de la config.
    query = ((db.mod.tipo.contains(ttip.mod_tipo)))  # seleccion kits del tipo
    if idcfg:
        query = query & (ttip.cfg == idcfg)
    else:
        query = query & (ttip.id == idcfgtip)
    # left a atributos del modulo y de la configuracion para  devolver todos los registros
    left = [db.mod_mod_atr.on(db.mod_mod_atr.mod == db.mod.id),
            tatr.on((tatr.atr == db.mod_mod_atr.atr) & (tatr.cfg == ttip.cfg) & (tatr.lock == False)),
            db.mod_atr.on(db.mod_atr.id == db.mod_mod_atr.atr),
            ttatr.on((ttip.id == ttatr.cfg_tip) & (ttatr.atr == db.mod_mod_atr.atr))]
    rows = db(query).select(db.mod.id, ttip.formula, tatr.atr, ttatr.atr, tatr.lock, tatr.valores, ttatr.valores,
                            db.mod_mod_atr.valores, db.mod_atr.tipo, ttip.mod_tipo, distinct=True, left=left,
                            orderby=(db.mod.id, ttip.mod_tipo))

    # buclea para comprar atributos
    mod = []
    lista = []
    excluye = False
    for row in rows:
        if [row.mod.id, row[ttip.mod_tipo], row[ttip.formula]] != mod and mod:
            if not excluye:
                lista.append(mod)
            else:
                excluye = False
        if not excluye:  # si ya hay un atributo de valores no coincidentes ya no comparo hasta cambio de kit
            if row[ttatr.atr] and row.mod_atr.tipo == MOD_ATR_TIPO.valores and row.mod_mod_atr.valores and row[
                ttatr.valores]:  # si hay coincidencia de atributos en tip_cfg y en modulo, proceso a ver si tienen valores comunes
                if not [item for item in row.mod_mod_atr.valores if item in row[ttatr.valores]]:
                    excluye = True
            elif row[tatr.atr] and row.mod_atr.tipo == MOD_ATR_TIPO.valores and row.mod_mod_atr.valores and row[
                tatr.valores]:  # si hay coincidencia de atributos en cfg y en modulo, proceso a ver si tienen valores comunes
                if not [item for item in row.mod_mod_atr.valores if item in row[tatr.valores]]:
                    excluye = True

        mod = [row.mod.id, row[ttip.mod_tipo], row[ttip.formula]]
    if not excluye and mod:
        lista.append(mod)
    if update:
        if idcfg:
            query = (db.mod_cfg_mod.cfg == idcfg)
        else:
            t = ttip(idcfgtip)
            idcfg = t.cfg
            query = ((db.mod_cfg_mod.mod_tipo == t.mod_tipo) & (db.mod_cfg_mod.cfg == idcfg))
        db(query).update(
            formula='-1')  # marco todos los componentes de la configuracion para luego borrr los no tocados
        for r in lista:
            db.mod_cfg_mod.update_or_insert(
                (db.mod_cfg_mod.cfg == idcfg) & (db.mod_cfg_mod.mod == r[0]) & (db.mod_cfg_mod.mod_tipo == r[1]),
                cfg=idcfg, mod=r[0], formula=r[2], mod_tipo=r[1])
        db(query & (db.mod_cfg_mod.formula == '-1')).delete()  # borro los que no han sido tocados
    return lista
"""

def formatea_multiple(lista):
    # formatea campo multipli con cada dato en un span recuadrado
    ret = []
    for i in lista:
        ret.append(SPAN(i,
                        _style='background-color: white; border: 1px solid black ; border-radius: 2px; padding: 1px; text-transform: lowercase; font-size: 12px;'))
        ret.append(SPAN(' '))
    return DIV(ret)

def cfgmod_genera_kits(db, idcfg=None, idcfgtip=None, update=True):
    """
    Devuelve una lista de los kits de un tipo de una plantilla de cfg y aplicar filtro general y despues el local
    idcfgtip es el id del
    """
    ttip = db.mod_mod_atr_cfg_tip_atr
    # filtro módulos de tipo ubicacion definidos en la plantilla de la config.
    if idcfg:
        query = (ttip.cfg == idcfg)
    else:
        idcfg = db.mod_cfg_tip(idcfgtip).cfg
        query = (ttip.cfg_tip == idcfgtip)
    rows = db(query).select(orderby=[ttip.mod,ttip.cfg_tip])  # rows con todos los kits seleccionados y atributos
    # RECORIENNDO todos los kits y si y comparar atributos con el cfgtip
    dentro = 0
    back=None
    kits=[]
    excluye=False
    for row in rows:
        def cumple(r):
            if not r.tip_valores==None and r.tipo == MOD_ATR_TIPO.valores and r.mod_valores:  # si hay coincidencia de atributos en tip_cfg y en modulo, proceso a ver si tienen valores comunes
                if [item for item in r.mod_valores if item in r.tip_valores]:
                    return True
                else:
                    return False

        # recorro los atributos y el último valor de cada atributo lo proceso, ya que es el del ultimo nivel
        if back:
            if back.mod!=row.mod  or back.cfg_tip!=row.cfg_tip:
                if not excluye:
                    kits.append(back)
                else:
                    excluye = False
        if row.tip_valores!=None and not excluye: #si ya esta excluido ignoramos hasta fin de modulo
             excluye = not cumple(row)
        back = row

    if update:
        if idcfgtip:
            t = db.mod_cfg_tip(idcfgtip)
            idcfg = t.cfg
            query = ((db.mod_cfg_mod.mod_tipo == t.mod_tipo) & (db.mod_cfg_mod.cfg == idcfg))
        else:
            query = (db.mod_cfg_mod.cfg == idcfg)
        db(query).update(
            formula='-1')  # marco todos los componentes de la configuracion para luego borrr los no tocados
        for r in kits:
            db.mod_cfg_mod.update_or_insert((db.mod_cfg_mod.cfg == idcfg) & (db.mod_cfg_mod.mod == r.mod) & (
                db.mod_cfg_mod.mod_tipo == r.mod_tipo), cfg=idcfg, mod=r.mod, formula=r.formula,
                                                mod_tipo=r.mod_tipo)
        db(query & (db.mod_cfg_mod.formula == '-1')).delete()  # borro los que no han sido tocados
    return kits

def premod_filtra_kits(db, pre):
    tatr = db.mod_pre_atr  # atributos de config
    ttip = db.mod_cfg_mod
    query = (ttip.cfg == db.mod_pre_nav.cfg) & (db.mod_pre_nav.pre == pre)

    # filtro módulos de las configuraciones elegidas en naves con atributos del presupuesto
    # left a atributos del modulo y de la configuracion para  devolver todos los registros
    left = [db.mod_mod_atr.on(db.mod_mod_atr.mod == ttip.mod),
            tatr.on((tatr.atr == db.mod_mod_atr.atr) & (tatr.pre == db.mod_pre_nav.pre)),
            db.mod_atr.on(db.mod_atr.id == db.mod_mod_atr.atr)]
    rows = db(query).select(ttip.mod, ttip.mod_tipo, ttip.formula, tatr.atr, tatr.valor, db.mod_mod_atr.valores,
                            db.mod_atr.tipo, distinct=True, left=left, orderby=(ttip.mod, ttip.mod_tipo))

    # buclea para comparar atributos
    mod = {}
    lista = []
    excluye = False
    for row in rows:
        mod0 = {'mod': row[ttip.mod], 'mod_tipo': row[ttip.mod_tipo], 'formula': row[ttip.formula]}
        if mod0 != mod and mod:
            if not excluye:
                lista.append(mod)
            else:
                excluye = False
        if not excluye:  # si ya hay un atributo de valores no coincidentes ya no comparo hasta cambio de kit
            if row[tatr.atr] and row.mod_atr.tipo == MOD_ATR_TIPO.valores and row.mod_mod_atr.valores and row[
                tatr.valor]:  # si hay coincidencia de atributos en pre y en modulo, proceso a ver si tienen valores comunes
                if not int(row[tatr.valor]) in row.mod_mod_atr.valores:
                    excluye = True
        mod = mod0
    if not excluye and mod:
        lista.append(mod)
    return lista

def cfgtip_propaga_hijos(cfg):
    """Copia los tipos de kits de una configuracion a sus hijos"""
    rows=db(db.mod_cfg_tip.cfg==cfg).select()
    hijos=db(db.mod_cfg.parent==cfg).select()
    if rows:
        for hijo in hijos:
            db(db.mod_cfg_tip.cfg==hijo.id).update(tag=0)
            for row in rows:
                db.mod_cfg_tip.update_or_insert(((db.mod_cfg_tip.cfg==hijo.id)&(db.mod_cfg_tip.mod_tipo==row.mod_tipo)),
                                                   cfg=hijo.id,
                mod_tipo=row.mod_tipo, min_mods=row.min_mods,formula=row.formula, tag=1)
            db((db.mod_cfg_tip.cfg == hijo.id)&(db.mod_cfg_tip.tag==0)).delete()

def mod_desarrolla_piezas(db, idmod):
    """Desarrolla las piezas de un kit desde las fórmulas indicadas a cantidades finales escalares usando atributos del propio kit
    """

    def graba_pie(pie, formula, nivel, mod):
        cantidad = Formula_ModAtr(db, idmod, formula=formula, kits=kits)() or 0
        if mod:
            kits[mod] = cantidad
        else:
            db.mod_pie_fin.insert(mod=idmod, cmp_pie=pie, formula=formula, cantidad=cantidad, nivel=nivel)

    row = db(db.mod_pie.mod == idmod).select(db.mod_pie.cmp_pie, db.mod_pie.cmp_mod, db.mod_pie.formula,
                                             db.mod_pie.cmp_pie, db.mod_pie.nivel,
                                             orderby=(db.mod_pie.nivel, db.mod_pie.cmp_pie))
    pie = None
    formula = ''
    kits = {}
    db(db.mod_pie_fin.mod == idmod).delete()
    if row:
        for r in row:
            if (r.cmp_pie or r.cmp_mod) != pie and pie:
                graba_pie(pie, formula, nivel, mod)
                formula = ''
            pie = r.cmp_pie or r.cmp_mod
            mod = r.cmp_mod
            nivel = r.nivel
            if formula:
                formula += '+'
            formula += r.formula
        graba_pie(pie, formula, nivel, mod)

def mod_desarrolla_piezas_old(db, idmod):
    """Desarrolla las piezas de un kit desde las fórmulas indicadas a cantidades finales escalares usando atributos del propio kit
    """

    def graba_pie(pie, formula, nivel, mod):
        cantidad = Formula_ModAtr(db, idmod, formula=formula, kits=kits)() or 0
        if mod:
            kits[mod] = cantidad
        else:
            db.mod_pie_fin.insert(mod=idmod, cmp_pie=pie, formula=formula, cantidad=cantidad, nivel=nivel)

    row = db(db.mod_pie.mod == idmod).select(db.mod_pie.cmp_pie, db.mod_pie.cmp_mod, db.mod_pie.formula,
                                             db.mod_pie.cmp_pie, db.mod_pie.nivel,
                                             orderby=(db.mod_pie.nivel, db.mod_pie.cmp_pie))
    pie = None
    formula = ''
    kits = {}
    db(db.mod_pie_fin.mod == idmod).delete()
    if row:
        for r in row:
            if (r.cmp_pie or r.cmp_mod) != pie and pie:
                graba_pie(pie, formula, nivel, mod)
                formula = ''
            pie = r.cmp_pie or r.cmp_mod
            mod = r.cmp_mod
            nivel = r.nivel
            if formula:
                formula += '+'
            formula += r.formula
        graba_pie(pie, formula, nivel, mod)

def mod_desarrolla_piezas( idmod,atr=None):
    """Desarrolla las piezas de un kit desde las fórmulas indicadas a cantidades finales escalares
    """

    def graba_pie(pie, formula, nivel, mod):
        cantidad = formul(formula=formula) or 0
        if mod:
            kits[mod] = cantidad
        else:
            if pie in piezas:
                piezas[pie].cantidad+=cantidad
                piezas[pie].formula= piezas[pie].formula+ '+'+piezas[pie].formula
            else:
                piezas[pie]=Storage(cmp_pie=pie, formula=formula, cantidad=cantidad, nivel=nivel)

    row = db(db.mod_pie.mod == idmod).select(db.mod_pie.cmp_pie, db.mod_pie.cmp_mod, db.mod_pie.formula,
                                             db.mod_pie.cmp_pie, db.mod_pie.nivel,
                                             orderby=(db.mod_pie.nivel, db.mod_pie.cmp_pie))
    pie = None
    formula = ''
    kits = {}
    piezas={}
    if atr:
        formul = Formula(atr, extravars=kits)
    else:
        formul = Formula_ModAtr( idmod, extravars=kits)
    db(db.mod_pie_fin.mod == idmod).delete()
    if row:
        for r in row:
            formul.extravars=kits
            if (r.cmp_pie or r.cmp_mod) != pie and pie:
                graba_pie(pie, formula, nivel, mod)
                formula = ''
            pie = r.cmp_pie or r.cmp_mod
            mod = r.cmp_mod
            nivel = r.nivel
            if formula:
                formula += '+'
            formula += r.formula
        graba_pie(pie, formula, nivel, mod)
    return piezas
