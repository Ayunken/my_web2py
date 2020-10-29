#!/usr/bin/env python
# -*- coding: utf-8 -*-
if False:
    from ..models.custom import *
    from ..models.basic_custom import *
    from ..models._kit import *
    from ..models.db import *


from gluon.storage import Storage
from decimal import Decimal, getcontext
import copy
from math import *

#CONSTANTES
#TODO Divisores canales tendría que estar en tres atributos globales secundarios: div_can_baj, div_can_sbj, div_can_cum,
# para que cada subtipo de canal pueda desarrollarse con diferentes opciones de longitudes (puede ocurrir que al externalizar la canal con bajante el makila no pueda fabricaralas de 6m y tengan que ser todas de 3

DIVISORES_CANALES={3.0:[6,3],2.5:[5,2.5],2.0:[6,4,2]} #por defecto, si los atributos lon_can_* no están suministrados, QUE ESTEN ORDENADOS INVERSAMENTE!!!


def redondea_si_float(v):
    #pasa a decimal los float (de forma recursiva en todos los contextos de valores)
    #v debe ser InverAtr
    def toDecimal(v):
        try:
            if isinstance(v, float):
                return Decimal('%s' % v)
        except:
            return v
        return v

    if isinstance(v, dict):
        for k, it in v.items():
            v[k] = redondea_si_float(v[k])
        return v
    if isinstance(v, list):
        for k in range(0, len(v)):
            v[k] = redondea_si_float(v[k])
        return v
    elif isinstance(v, PresupAtrsValor):
        v.value = redondea_si_float(v.value)
        return v
    elif isinstance(v, float):
        #return Decimal('%s' % v)
        return round(v,3) #ATENCION TODO a 3 decimales máximo
    return v


class InverNodo(object):
    def __init__(self,t,m):
        self.m=m
        self.t=t
        self.canal_izq=None
        self.canal_der=None

class TipoCanal():
    izq,der,med=0,1,2
    nor,cum,baj=0,10,20
    def subtipo(self,tipo):
        if tipo>=self.baj:
            return self.baj
        elif tipo>=self.cum:
            return self.cum
        else:
            return self.nor
class BloqueItem(list):
    def __init__(self,longitud,unidades):
        self.append(longitud)
        self.append(unidades)
        self.longitud = self[0]
        self.unidades = self[1]


def divisores_canales( tipo,atrs):
    if tipo >= TipoCanal.baj:
        atr = ATRS.lon_can_cbj
    elif tipo >= TipoCanal.cum:
        atr = ATRS.lon_can_cum
    else:
        atr = ATRS.lon_can_sbj
    return atrs[atr].value

class ItemTramo():
    """Clase de componentesde Tramos """
    def __init__(self,tipo,mods,bloques=None):
        self.mods=mods
        self.tipo=tipo
        self.bloques=bloques or []

    def add_bloque(self,bloque):
        self.bloques.append(bloque)

    def desarrolla(self, sep,largos):
        long = sep * self.mods
        for l in largos:
            if long:
                div = int(long / l)
                if div > 0:
                    self.add_bloque(BloqueItem(l, div))
                    long -= div * l
class Tramo(list):
    """clase para calcular tramos de canal. las unidades, pos, etc. son módulos 1 modulo = separacion"""
    def __init__(self,sep):
        self.sep=sep

    def add_tipo(self,tipo,cantidad=1):
        """Añade uds al ultimo tipo si coincide,y si no abre un nuevo"""
        if self:
            if self[-1].tipo == tipo:
                self[-1].mods += cantidad
                return
        self.append(ItemTramo(tipo,cantidad))
    def len(self):
        """Devuelve la longitud en modulos"""
        suma=0
        for i in self:
            suma += i.mods
        return suma

    def count(self,tipo):
        """devuelve diccionario de las longitudes de cada tipo
        """
        from collections import Counter
        res=Counter()
        for i in self:
            if i.tipo==tipo:
                for j in i.bloques:
                    d={j[0]:j[1]}
                    res += Counter(d)
        return res
    def inserta_tipo(self,tipo,pos,atrs,sep=None):
        """Quita la canal de menor tamaño en el subtramo de la pos, la convierte en otro subtramo que inserta
        Está pensado para insertar la canal cumbrera y bajantes
        """
        if not sep:
            sep=self.sep
        divisores=divisores_canales(tipo,atrs)
        ac=0
        for i,v in enumerate(self):
            if v.mods+ac-1 >= pos:
                if len(v.bloques)==0:
                     v.bloques=[0,0]
                j=None
                for n in reversed(v.bloques): #busco hanchos compatibles
                    if n[0] in divisores:
                        j=n
                        break
                if not j:
                    #hay que partir alguna canal de sin baj en 2
                    divisor=divisores[-1] #tomamos la medida más pequeña para insertar la canal cumb/baj
                    v.bloques[-1][1]-=1 #resto una canal . tomamos el bloque de medida más pequeño existente (si hubiera de 6 y 4, cuando la baj ha de ser de 2 , p.e.
                    resto=v.bloques[-1][0]-divisor #tomo del bloque existente la medida ultima y le resto
                    if resto == divisor:
                        v.bloques.append([divisor, 2])  # añado 2 canales del mismo tamañao
                        j=v.bloques[-1] #el ultimo es pues donde queda disponible canales del tamaño adecuado
                    else:
                        if resto < divisor: #si lo que queda es MENOR que el divisor, hay que ponerlo el último
                            v.bloques.append([divisor, 1])
                            v.bloques.append([resto, 1])  # añado rel resto como ultima medida disponible
                            j = v.bloques[-2] #ya tengo pues medida del divisor en el penultimo
                        else:
                            v.bloques.append([resto, 1])
                            v.bloques.append([divisor, 1])  # añado rel resto como medida disponible
                            j=v.bloques[-1] #ya tengo pues medida en el ultimo
                modulos=j[0]/sep
                #aqui está la clave
                #si el ultimo modulo es de una medida compatible con lo que se quiere poner ok
                #si no hay que ignorarlo y buscar otro
                j[1]-=1 #resto una canal de ese largo
                v.mods-=modulos#le resto los modulos afectados
                trm=ItemTramo(tipo+v.tipo,modulos,[BloqueItem(j[0],1)]) #el tipo se combina con el tipo existente
                if j[1] == 0:
                    del  v.bloques[-1]  # si no hay más de esea longtiud, lo elimino

                if ac==pos:#si la canal a sustituir va al inicio o al final del este tramo, no hará falta dividir
                    self.insert(i, trm)  # inserto el tramo antes
                elif ac+v.mods+modulos-1==pos:
                    self.insert(i+1,trm) #inserto el tramo despues
                else: #queda por el medio, habrá que dividir el tramo
                    self.insert(i + 1, trm)  # inserto el tramo cumbrera tras el tramo completo
                    trozo1=pos-ac
                    r=v.mods-trozo1
                    if trozo1>0: #si hay modulos tras la pos, pongo ese resto en un tramo que agrego despues de cumbrera
                        restodes = []
                        for k in reversed(v.bloques):
                            if k[1]:
                                if trozo1<k[0]*k[1]/sep and trozo1>0:
                                    r=k[1]*k[0]/sep-trozo1
                                    uds=int(r / k[0]*sep)
                                    restodes.append(BloqueItem(k[0],uds))
                                    k[1]-=uds
                                    v.mods-=r
                                    if not k[1]:
                                        del v.bloques[-1]
                                    trozo1-= r
                        trmres=ItemTramo(v.tipo,r,restodes)
                        self.insert(i + 2, trmres)  # inserto el tramo restante dividido
                return True
            ac += v.mods
    def desarrolla(self,largos):
        """Convierte los modulos en canales de longitudes varias"""
        for i in self:
            i.desarrolla(self.sep,largos)
    def desempaqueta_canales(self):
        """desarrolla todas canales en todo el tramo
        Devuelve una lista de diccionarios, cada elemento con tipo de canal y longitud
        """
        tramo=[]
        for t in self:
            if t==self[-1] and len(self) >1: # si es el último tramo lo itero al revés para que las canales de longitud menor queden en el medio
                rango=reversed(t.bloques)
            else:
                rango=t.bloques
            for c in rango:
                for i in c[1]:
                    canal=Storage(tipo=t.tipo,largo=c[0])
                    tramo.append(canal)
        return tramo
class PresupAtrsValor():
    value=None
    idvalue=None
    def __init__(self,value=None,idvalue=None):
        self.value=value
        self.idvalue=idvalue
class PresupAtrs(dict):
    subnave0=0
    mod_tipo0=IDRAIZ_MOD_TIPO
    parents={}
    def __init__(self,presupuestoId,db):
        self.presupuestoId=presupuestoId
        self._db=db
        self.subnave=self.subnave0
        self.mod_tipo=self.mod_tipo0
    def get_value_context(self, atr_id, subnave=None, mod_tipo=None): #@atr aqui es id
        if subnave==None:
            subnave=self.subnave
        if mod_tipo==None:
            mod_tipo=self.mod_tipo
        if atr_id in self:
            return self._get_value_context(self[atr_id],subnave,mod_tipo)
    def _get_value_context(self,atr,subnave, mod_tipo): #atr es typo InverAtr
        valor = PresupAtrsValor()
        if subnave in atr.valores:
            valor=  self._find_in_parents(atr, subnave, mod_tipo)
        if valor.value == None:
            return self._find_in_parents(atr, self.subnave0, mod_tipo)
        else:
            return valor
    def set_context(self,subnave,mod_tipo=None):
        if mod_tipo==None:
            mod_tipo=self.mod_tipo0
        for atr in self.values():
            if 'valores' in atr:
                oldvalue = self._get_value_context(atr, self.subnave, self.mod_tipo).value
                if atr.value!=oldvalue:
                    self.add(atr.value,subnave=self.subnave,mod_tipo=self.mod_tipo,id=atr.id)
                valor=self._get_value_context(atr,subnave,mod_tipo)
                atr.value,atr.idvalue=valor.value,valor.idvalue
        self.subnave = subnave
        self.mod_tipo = mod_tipo
    def _find_in_parents(self,atr,subnave,mod_tipo):
        if subnave not in atr.valores:
            return PresupAtrsValor()
        if mod_tipo in atr.valores[subnave]:
            return atr.valores[subnave][mod_tipo]
        else:
            if not mod_tipo in self.parents:
                mt= db.mod_tipos(mod_tipo)
                if mt:
                    self.parents[mod_tipo]=mt.parent
                else:
                    raise Exception( 'Mod_tipo %s not exist'%mod_tipo)
            padre=self.parents[mod_tipo]
            if padre:
                return self._find_in_parents(atr,subnave,padre)
            else:
                return PresupAtrsValor()
    def load_atrs(self):
        db = self._db
        tabla=db.mod_pre_atr
        campos=[tabla[i] for i in ('id','atr','subnave','valor','tipo','mod_tipo')]
        campos.append(db.mod_tipos.parent)
        rows = db((tabla.pre == self.presupuestoId)&(db.mod_tipos.id==tabla.mod_tipo)&(db.mod_atr.id==tabla.atr)).select(orderby=[tabla.subnave,tabla.mod_tipo])
        for r in rows:
            if r[tabla.tipo] == MOD_ATR_TIPO.valores and r[tabla.valor]:
                rv = db.mod_val(r[tabla.valor])
                if rv:
                    v=rv.valor
                    idv=rv.id
                else:
                    continue
            else:
                v = Formula_Pre(self._db, self.presupuestoId, r[tabla.valor])()
                idv=None
            self.add(v, r[tabla.subnave],r[tabla.mod_tipo],idvalue=idv,**r.mod_atr)
            self.parents[r[tabla.mod_tipo]] =r.mod_tipos.parent
        for k, v in ATRS.items():  # el valor (v) de cada item es el id del atributo, k=nombre de variable en Storage ATRS
            if v not in self:
                r = self._db.mod_atr(v)
                if r:
                    self.add(None,self.subnave0,self.mod_tipo0, **r)
                else:
                    self.add(None,self.subnave0,self.mod_tipo0, id=v)
    def add(self,value,subnave=None,mod_tipo=None, idvalue=None,**attr):
        if subnave==None: subnave=self.subnave0
        if mod_tipo==None: mod_tipo=self.mod_tipo0
        id = attr.get('id')
        if not id in self:
            tipo = attr.get('tipo')
            key = attr.get('clave') or attr.get('key')
            name = attr.get('name')
            self[id] = InverAtr(value, key=key, name=name, tipo=tipo, id=id,idvalue=idvalue)
            self[id].valores = {subnave:{mod_tipo: PresupAtrsValor(value,idvalue)}} #inicializamos valores
        else:
            if not subnave in self[id].valores:
                self[id].valores[subnave]={}
            self[id].valores[subnave][mod_tipo]=PresupAtrsValor(value,idvalue)

class Invernadero(object):
    #constantes de proyecto
    def __init__(self,db,presupuestoId ):
        self.presupuestoId =  presupuestoId
        self._db=db
        self.pre = self._db(db.mod_pre.id == self.presupuestoId)
        self.atr = PresupAtrs(presupuestoId,db)
        self.atr.load_atrs()
        self.atr.add([],id=0,name='error',key='err')
        self.tuneles=None
    def __call__(self):
        self.tuneles,self.matriz=self._calculamatriz()
        if  len(self.tuneles)>0:
            self._calcula_atributos_internos()
        return self
    def _init_dict(self, item, keys):
        item.value = {}
        for key in keys:
            item.value[key] = 0
    def _error_add(self,txt):
        self.atr[0].value.append(txt)
    def _calculamatriz(self):
        rows = self._db(self._db.mod_pre_nav.pre == self.presupuestoId).select(orderby=self._db.mod_pre_nav.posx)
        tuneles,maxmodulos,db=([],0,self._db)
        sep = float(self.atr[ATRS.separacion_vanos].value or 0)
        self.atr[ATRS._matriz_ancho].value = 0
        self.anchos = []
        cfg,tund,tunh=None,1,0
        #PRIMERO GENERAMOS LOS TÚNELES
        tabsub=db.mod_pre_subnaves
        db(tabsub.pre==self.presupuestoId).update(cfg=-1)
        def addsubtun():
            sub=tabsub.update_or_insert((tabsub.pre == self.presupuestoId) & (tabsub.tund == tund),
                                       pre=self.presupuestoId, tund=tund, tunh=tunh, cfg=cfg)
            if not sub:
                sub = tabsub((tabsub.pre == self.presupuestoId) & (tabsub.tund == tund))
            recolectar_atributos_presupuesto2(db,self.presupuestoId,self.atr,cfg,sub.id)

        for r in rows:
            self.atr[ATRS._matriz_ancho].value+= r.unidades*float(r.anchonave.valor)
            if cfg != r.cfg and cfg!=None:
                addsubtun()
                tund=tunh+1
            cfg = r.cfg
            tunh+=r.unidades
            for t in range(0,r.unidades):
                tuneles.append(Storage(posy= r.posy, posmod=r.posy/sep ,longitud=r.longitud, largomod=r.longitud/sep,anchonave= float(r.anchonave.valor)))
                if not r.anchonave.valor in self.anchos:
                    self.anchos.append( r.anchonave.valor)
                if r.posy+r.longitud>maxmodulos:
                    maxmodulos=r.posy+r.longitud
        addsubtun()
        db((tabsub.pre == self.presupuestoId )& (tabsub.cfg==-1)).delete()

        if not sep:
            return
        #AHORA GENERAMOS LA MATRIZ
        maxmodulos=maxmodulos/sep
        maxmodulos=int(maxmodulos)
        self.atr[ATRS._nmodulos].value = maxmodulos
        self.atr[ATRS._matriz_largo].value = maxmodulos * sep
        self.atr[ATRS._ntuneles].value = len(tuneles)
        matriz = []
        for k,t in enumerate(tuneles):
            tunel=[]
            for m in range(0,maxmodulos):
                pos=m*sep
                if pos>=t['posy'] and pos<t['posy']+t.longitud:
                    tunel.append(InverNodo(k,m))
                else:
                    tunel.append(None)
            matriz.append(tunel)
        return tuneles,matriz
    def __str__(self):
        if self.matriz:
            cad=''
            for t in self.matriz:
                for m in t:
                    cad+='1' if m['ocupado'] else '0'
                cad+="\n"
            return cad
    def _posrel(self,mod,pos=None,m=None,t=None):
        #devuelve True si hay modulo enla posicion None=centro, resto 'n s e w nw ne sw se'
        x=self.matriz
        if mod:
            m=mod.m
            t=mod.t
        if not pos:
            return (x[t][m]!=None)
        if pos=='s':
            return False if m == 0 else (x[t][m-1]!=None)
        elif pos == 'sw':
            return False if t==0 or m == 0 else (x[t-1][m-1]!=None)
        elif pos == 'se':
            return False if  t==len(x)-1 or m == 0 else (x[t+1][m-1] !=None)
        elif pos=='n':
            return False if m == len(x[t]) - 1 else (x[t][m+1]!=None)
        elif pos == 'nw':
            return False if t==0 or m == len(x[t]) - 1 else (x[t-1][m+1]!=None)
        elif pos == 'ne':
            return False if t==len(x)-1 or m == len(x[t]) - 1 else (x[t+1][m+1]!=None)
        elif pos == 'w':
            return False if t == 0 else (x[t-1][m] != None)
        elif pos == 'e':
            return False if t == len(x) - 1 else (x[t+1][m] != None)
    def _clearAtrs(self,lista):
        for i in lista:
            if self.atr[i].tipo==MOD_ATR_TIPO.vector:
                self.atr[i].value = []
            elif self.atr[i].tipo == MOD_ATR_TIPO.diccionario:
                self.atr[i].value = {}
            else:
                self.atr[i].value=0
    def _calcula_atributos_internos(self):
        tabla=db.mod_pre_subnaves
        rows = db(tabla.pre==self.presupuestoId).select(orderby=[tabla.tund,tabla.modd])
        for r in rows:
            self.atr.set_context(subnave=r.id)
            self._calcula_atributos_internos0(r)
    def _calcula_atributos_internos0(self,rango):

        def tramo_anade_ancho(v):
            if not v.value:
                v.value= [0]
            v.value[-1] += float(ancho)

        def tramo_corta_ancho(v): # no gastos subindices de ancho, ya que cada iteracion subnave llevaá un ancho diferente
            if v.value:
                if v.value[-1]:
                    v.value.append(0)
        """
        def tramo_anade_ancho_old(
                v):  # no gastos subindices de ancho, ya que cada iteracion subnave llevaá un ancho diferente
            if not v.value[ancho]:
                v.value[ancho] = [0]
            v.value[ancho][-1] += float(ancho)

        def tramo_corta_ancho_old(v):
            if v.value[ancho]:
                if v.value[ancho][-1]:
                    v.value[ancho].append(0)
        """
        def tramo_anade(v):
            if not v.value:
                v.value=[0]
            v.value[-1] += sep_vanos

        def tramo_corta(v):
            if v.value:
                if v.value[-1]:
                    v.value.append(0)

        if rango.modd==None:
            rango.modd=1
        maxmodulos= self.atr[ATRS._nmodulos].value
        if rango.modh==None:
            rango.modh=maxmodulos
        #controles minimos para comprobar valores de atributos que luego no casquen
        if not self.atr[ATRS.separacion_vanos].value:
            return

        #INICIALIZACION DE ATRIBUTOS
        self._clearAtrs([ATRS._nod_esq_ext_izq,ATRS._nod_esq_ext_der,ATRS._nod_esq_int_der,ATRS._nod_esq_int_izq,ATRS._nod_frn_ali,ATRS._nod_lat_din_izq,ATRS._nod_lat_din_der,
                         ATRS._nod_lat_sab_izq,ATRS._nod_lat_sab_der,ATRS._nod_int_sab,ATRS._nod_int_din, ATRS._seg_lon_ext,ATRS._seg_lon_med,ATRS._seg_tra_din_med,ATRS._seg_tra_din_lat,ATRS._seg_tra_sab_med,ATRS._seg_tra_sab_lat,
                         ATRS._trm_cor_lat_izq,ATRS._trm_cor_lat_der,ATRS._trm_can])
        #inicialilzar diccionarios
        #self._clearAtrs([ATRS._trm_can])
        #inicializar diccionarios con anchos de nave
        #[self._init_dict(self.atr[i],self.anchos) for i in (ATRS._seg_frn_ext, ATRS._seg_frn_med,ATRS._trm_cor_frn)]
        self._clearAtrs([ATRS._seg_frn_ext, ATRS._seg_frn_med,ATRS._trm_cor_frn])
        var=self.atr
        pos = self._posrel

        #calculo si lineasable es impar (1) o par(0)
        sep_vanos = float(self.atr[ATRS.separacion_vanos].value)
        lineasable=divmod(float(self.atr[ATRS._lin_sable].value)/sep_vanos,2)[1]
        if not var[ATRS.bajantes].value:
            var[ATRS.bajantes].value=999  # bajante cada x metros (si no esá definido se pone un número grande para que no haga nada
        doblependiente = True if var[ATRS.pendiente].value == '2' else False
        if doblependiente:
            if not var[ATRS.pospte].value:  # posicion Y en metros de la cumbrera cuando doble pendiente
                var[ATRS.pospte].value=int(var[ATRS._matriz_largo].value/2/sep_vanos)*sep_vanos
                # posicion Y en metros de la cumbrera cuando doble pendiente
        #recorrido longitudinal túnel a túnel (abajo a arriba y de izq. a drcha.
        for idt in range(rango.tund-1,rango.tunh):
            t=self.matriz[idt]
            tramo_corta(var[ATRS._trm_cor_lat_der]) #inicializacion de tramos
            tramo_corta(var[ATRS._trm_cor_lat_izq])
            for idm in range(rango.modd-1,rango.modh):
                m=t[idm]
                if m:
                    ancho=str(self.tuneles[idt].anchonave)
                    sable=(divmod(idm, 2)[1] != lineasable)
                    ################# NODOS #####################################
                    if sable:
                        if pos(m, 'n'):
                            if not pos(m,'w'):
                                if not pos(m,'nw'):
                                    var[ATRS._nod_lat_sab_izq].value+= 1
                                    var[ATRS._nod_int_sab].value += 1  # en el tunel de izq. meto los interiores de su derecha
                            elif not pos(m, 'e'):
                                if not pos(m,'ne'):
                                    var[ATRS._nod_lat_sab_der].value+= 1
                            else: #interior
                                var[ATRS._nod_int_sab].value += 1
                    else:
                        if pos(m, 'n'):
                            if not pos(m,'w'):
                                if not pos(m,'nw'):
                                    var[ATRS._nod_lat_din_izq].value+= 1
                                    var[ATRS._nod_lat_din_der].value += 1
                            elif not pos(m, 'e'):
                                if not pos(m,'ne'):
                                    var[ATRS._nod_int_din].value += 1
                            else:  # interior
                                var[ATRS._nod_int_din].value += 1
                    if not pos(m, 'n'):
                        ################  NODOS ESQUINA #####################
                        if not pos(m,'w'):
                            var[ATRS._nod_esq_ext_izq].value+= 1 #esquina
                        if not pos(m, 'e'):
                            var[ATRS._nod_esq_ext_der].value += 1
                        elif not pos(m, 'ne'):
                            var[ATRS._nod_frn_ali].value += 1
                        if pos(m, 'nw'):
                            var[ATRS._nod_esq_int_izq].value += 1
                        if pos(m, 'ne'):
                            var[ATRS._nod_esq_int_der].value += 1
                        ################  SEGMENTOS #####################
                        if not pos(m, 'w'):
                            #var[ATRS._seg_frn_ext].value[ancho] += 1
                            var[ATRS._seg_frn_ext].value += 1
                        elif not pos(m, 'e'):
                            var[ATRS._seg_frn_ext].value += 1
                            #var[ATRS._seg_frn_ext].value[ancho] += 1
                        else:
                            #var[ATRS._seg_frn_med].value[ancho] += 1
                            var[ATRS._seg_frn_med].value += 1
                    else:  # el de arriba está ocupado
                        if not pos(m,'w'):  # segmentos transversales se cuenta el seg superior  de todos los mods menos el del ultimo de arriba
                            var[ATRS._seg_tra_sab_lat if sable else ATRS._seg_tra_din_lat].value += 1
                        elif not pos(m, 'e'):
                            var[ATRS._seg_tra_sab_lat if sable else ATRS._seg_tra_din_lat].value += 1
                        else:
                            var[ATRS._seg_tra_sab_med if sable else ATRS._seg_tra_din_med].value += 1

                    if not pos(m, 's'):
                        ################  NODOS ESQUINA #####################
                        if not pos(m, 'w'):
                            var[ATRS._nod_esq_ext_izq].value += 1
                        if not pos(m, 'e'):
                            var[ATRS._nod_esq_ext_der].value += 1
                        elif not pos(m, 'se'):
                            var[ATRS._nod_frn_ali].value += 1
                        if pos(m, 'sw'):
                            var[ATRS._nod_esq_int_izq].value += 1
                        if pos(m, 'se'):
                            var[ATRS._nod_esq_int_der].value += 1
                        ################  SEGMENTOS #####################
                        if not pos(m,'w'):
                            #var[ATRS._seg_frn_ext].value[ancho] += 1
                            var[ATRS._seg_frn_ext].value+= 1
                            var[ATRS._seg_lon_ext].value += 1
                            if not pos(m,'e'):
                                var[ATRS._seg_lon_ext].value += 1 #luz unica
                        elif not pos(m,'e'):
                            var[ATRS._seg_frn_ext].value+= 1
                            #var[ATRS._seg_frn_ext].value[ancho] += 1
                            var[ATRS._seg_lon_ext].value += 1
                            var[ATRS._seg_lon_med].value += 1 #este es el segmento izquierdo del ultimo modulo de la derecha
                        else:
                            var[ATRS._seg_frn_med].value += 1
                            #var[ATRS._seg_frn_med].value[ancho] += 1
                            var[ATRS._seg_lon_med].value += 1 #segmento izquierdo de todos los interiores
                    #CANALES Y CORREAS
                    #DEBERIA IDENTIFICAR CUANDO LLEGAMOS A LA CUMBRERA (SI HAY) PARA EMPEZAR NUEVO TRAMO
                    #LAS BAJANTES, LUEGO SOLO SERÍA CAMBIAR UNA POR CON BAJANTE (PRIMERO LAS MÁS PEQUEÑAS)
                    if not pos(m,'w'):
                        tramo_anade(var[ATRS._trm_cor_lat_izq])
                    else:
                        tramo_corta(var[ATRS._trm_cor_lat_izq])
                    if not pos(m, 'e'):
                        tramo_anade(var[ATRS._trm_cor_lat_der])
                    else:
                        tramo_corta(var[ATRS._trm_cor_lat_der])

                else: # modulo vacio
                    pass
        #FIN BUCLE tuneles del invernadero
        #transversal, fila a fila, de izq a derecha y de abajo a arriba
        for i in range(rango.modd-1,rango.modh):
            if i>0:
                tramo_corta_ancho(var[ATRS._trm_cor_frn])  # inicializacion de tramos
            for idt in range(rango.tund-1,rango.tunh):
                t=self.matriz[idt]
                m=t[i]
                if m:
                    ancho = str(self.tuneles[m.t].anchonave)
                    if not pos(m, 'n') or not pos(m,'s'):
                        # Tramos frontales
                        tramo_anade_ancho(var[ATRS._trm_cor_frn])
                    else:
                        tramo_corta_ancho(var[ATRS._trm_cor_frn])
                else:
                    tramo_corta_ancho(var[ATRS._trm_cor_frn])

        """
        for i in [ATRS._trm_cor_frn]:
            for k,v  in var[i].value.items(): #quito ceros del final de la lista
                if isinstance(v,list):
                    if not v[-1]:
                        var[i].value[k].remove(v[-1])
        """
        for i in (ATRS._trm_cor_lat_izq, ATRS._trm_cor_lat_der,ATRS._trm_cor_frn):
            if isinstance(var[i].value, list):
                if not var[i].value[-1]:
                    var[i].value.remove(var[i].value[-1])
        self._calcula_canales(rango)
        self.redondea_floats()
    def _calcula_canales(self,rango):
        """Calculo de CANALES
        """
        var = self.atr  # alias abreviados
        pos = self._posrel
        sep = float(var[ATRS.separacion_vanos].value)
        tramos=[]
        pendiente=int(var[ATRS.pendiente].value)
        #comprueba largos canales disponibles, los ordeno inversamente
        for i in (ATRS.lon_can_cbj, ATRS.lon_can_cum, ATRS.lon_can_sbj):
            if i in var:
                if not isinstance(var[i].value,list):
                    var[i].value=[var[i].value]
                var[i].value=list(reversed(sorted(var[i].value)))
            else:
                var[i].value = DIVISORES_CANALES[sep]
        if  pendiente== TipoPendiente.doble:
            poscumbrera = int(var[ATRS.pospte].value / sep)
        else:
            poscumbrera = False
        for idt in range(rango.tund - 1, rango.tunh):
            t=self.matriz[idt]
            tramo = Tramo(sep)  # aqui almaceno los segmentos que hay de cada tipo (inicial izq, inci.der, intermedio, final izq y final der)
            if idt == 0:
                tramo0 = Tramo(sep)
            else:
                tramo0 = None
            for idm in range(rango.modd - 1, rango.modh): #POR AHORA SUBNAVES deberían ser de TUNEL COMPLETO, porque las canales sería difícil calcularlas
                m=t[idm]
                lastidm=None #me guardo la ultima posicion ocupada en el tunel (para saber la ultima posicion para la bajante de arriba)
                if m:
                    if m.t == 0:  # es el primer tunel
                        tramo0.add_tipo(TipoCanal.izq)
                    if not pos(m, 'e'):
                        tramo.add_tipo(TipoCanal.der)
                    else:
                        tramo.add_tipo(TipoCanal.med)
                    lastidm=idm
                else:  # modulo vacio
                    if pos(None, 'e', m=idm, t=idt):
                        tramo.add_tipo(TipoCanal.der)
            # ahora se convierten los modulos en canales segun largos
            tramo.desarrolla( divisores_canales(tramo[-1].tipo,self.atr))
            if tramo0!=None:
                tramo0.desarrolla( divisores_canales(tramo[-1].tipo,self.atr))
            #calculos previos de cumbreras y bajantes
            if pendiente== TipoPendiente.doble and \
                        poscumbrera < self.tuneles[idt].largomod + self.tuneles[idt].posmod and\
                        poscumbrera > self.tuneles[idt].posmod:
                poscum = int(poscumbrera - self.tuneles[idt].posmod)
                # poscum es la posicion de la cumbrera relativa al tramo
                tramo2=tramo.len()-poscum
            else:
                poscum=int(tramo.len())
                tramo2=tramo.len()
            tramo1=tramo.len()-tramo2
            total = int(tramo.len())
            if var[ATRS.bajantes]:
                cada = int(var[ATRS.bajantes].value / sep)
                nbajtramo1= int(ceil(tramo1/float(cada))-1)
                nbajtramo2 = int(ceil(tramo2 / float(cada)) - 1)
                if nbajtramo1:  # colocamos primero bajantes tramo 1, ya qe este no varía por la cumbrera
                    for posicion in range(cada, poscum, cada):
                        tramo.inserta_tipo(TipoCanal.baj, posicion,atrs=self.atr)
                        if tramo0:
                            tramo0.inserta_tipo(TipoCanal.baj, posicion,atrs=self.atr)
            else:
                nbajtramo1=nbajtramo2=0

            def coloca_bajantes2():
                if nbajtramo2:  # bajantes tramo 2
                    for posicion in range(poscum + cada, total, cada):
                        tramo.inserta_tipo(TipoCanal.baj, posicion, atrs=self.atr)
                        if tramo0:
                            tramo0.inserta_tipo(TipoCanal.baj, posicion, atrs=self.atr)
            def coloca_cumbrera():
                if poscum < total:  # colocamos cumbrera
                    # la posicion de la cumbrera define el final del tramo1, que no se toca, y se coloca la cumbrera en el principio del tramo2
                    tramo.inserta_tipo(TipoCanal.cum, poscum, atrs=self.atr)
                    if tramo0 != None:
                        tramo0.inserta_tipo(TipoCanal.cum, poscum, atrs=self.atr)
            #ahora dependiendo de las longitudes de bajantes disponibles, situamos primero las bajantes o la cumbrera del tramo2
            if len(var[ATRS.lon_can_cbj].value) < len(var[ATRS.lon_can_cum].value):  # prioridad bajantes
                coloca_bajantes2()
                coloca_cumbrera()
            else:
                coloca_cumbrera()
                coloca_bajantes2()
            if tramo0!=None:
                tramos+=[tramo0]
            tramos+=[tramo]
        # Carga de resultados en variable canales
        d = {}
        for i in DIVISORES_CANALES[sep]:
            d[i] = 0
        from collections import Counter
        d=Counter()
        subc = Storage(sbj=d.copy(), cbj=d.copy(), cum=d.copy(),totm=0.0, totuds=0)
        var[ATRS._canales].value = Storage(der=copy.deepcopy(subc), izq=copy.deepcopy(subc), med=copy.deepcopy(subc),baj=0,tap=0)
        vcan = var[ATRS._canales].value
        for i in tramos:
            vcan.der.sbj += i.count(TipoCanal.der)
            vcan.der.cbj += i.count(TipoCanal.der+TipoCanal.baj)
            vcan.der.cum += i.count(TipoCanal.der + TipoCanal.cum)
            vcan.izq.sbj += i.count(TipoCanal.izq)
            vcan.izq.cbj += i.count(TipoCanal.izq + TipoCanal.baj)
            vcan.izq.cum += i.count(TipoCanal.izq + TipoCanal.cum)
            vcan.med.sbj += i.count(TipoCanal.med)
            vcan.med.cbj += i.count(TipoCanal.med + TipoCanal.baj)
            vcan.med.cum += i.count(TipoCanal.med + TipoCanal.cum)
            var[ATRS._trm_can].value.append(sum([j.mods for j in i]))
        totcumbreras=vcan.izq.cum+vcan.der.cum+vcan.med.cum
        totcumbreras=sum(totcumbreras.values())
        vcan.baj += len(tramos)+ totcumbreras
        vcan.tap += len(tramos) - totcumbreras
        #Chequeo de longituds. Todas las canales deben sumar la suma de longitudes de todos los tuneles mas la longtiud del tunel 0
        suma=Counter()
        for i in ('der','izq','med'):
            for j in ('sbj','cbj','cum'):
                suma  += vcan[i][j]
                vcan[i].totm += sum([k * v for k, v in vcan[i][j].items()])
                vcan[i].totuds += int(sum([v for k, v in vcan[i][j].items()]))
                vcan[i][j]=dict(vcan[i][j]) #los convierto de tipo Counter a dict no vaya a tener problemas luego si se filtra por tipo a de ser dict
        #comprobaciones
        metroscanal=metrostun=0
        for k,v in suma.items():
            metroscanal+=float(k)*v
        for i in range(0,len(self.tuneles)):
            l=self.tuneles[i].longitud
            if i<len(self.tuneles)-1:
                if self.tuneles[i+1].longitud>self.tuneles[i].longitud:
                    l=self.tuneles[i+1].longitud
            metrostun += l
        metrostun += self.tuneles[0].longitud
        vcan.totm=metroscanal
        vcan.totuds =int(sum(v for k,v in suma.items()))
        vcan.totmteorico=metrostun
        if metrostun!=metroscanal:
            self._error_add('Metros canales ({0}) difiere de metros tuneles ({1})'.format(metroscanal,metrostun))
    def _guarda_kits(self, kits, subnave):
        formul = Formula(self.atr)  # el contexto ya lo hemos cambiado antes
        for kit in kits:
            res = formul(kit['formula'])
            mod = db.mod_pre_mod((db.mod_pre_mod.subnave == subnave) & (db.mod_pre_mod.pre == self.presupuestoId) & (
            db.mod_pre_mod.mod == kit['mod']) & (
                                     db.mod_pre_mod.mod_tipo == kit['mod_tipo']))
            if mod:
                mod.update_record(cantidad=(res or 0) + (mod.cantidad or 0))
            else:
                db.mod_pre_mod.insert(pre=self.presupuestoId, subnave=subnave, mod=kit['mod'], mod_tipo=kit['mod_tipo'],
                                      cantidad=res)
    def calcula_kits(self):
        tabla = db.mod_pre_subnaves
        db(db.mod_pre_mod.pre == self.presupuestoId).update(cantidad=None)
        rows = db(tabla.pre == self.presupuestoId).select(orderby=[tabla.tund, tabla.modd])
        for r in rows:
            self.atr.set_context(r.id) #no creo que haya que ir cambiando el contexto para cada tipo de kit
            kits=self.select_kits_filtrados(r.id,r.cfg)
            self._guarda_kits(kits,r.id)

        db((db.mod_pre_mod.pre == self.presupuestoId) & (db.mod_pre_mod.cantidad == None)).delete()
    def calcula_piezas(self):
        kits= db(db.mod_pre_mod.pre == self.presupuestoId).select(orderby=db.mod_pre_mod.subnave)
        piezas={}
        db(db.mod_pre_mod_pie.pre==self.presupuestoId).delete()
        for kit in kits:
            if kit['cantidad']:
                self.atr.set_context(kit.subnave,kit.mod_tipo)
                pz=mod_desarrolla_piezas(kit['mod'],self.atr)
                #current.logger.debug('Kit:%s: Pz: %s' % (kit['mod'], pz))
                for k,p in pz.items():
                    if p.cantidad:
                        cantidad=float(p.cantidad) * kit['cantidad']
                        if p.cmp_pie in piezas:
                            piezas[p.cmp_pie] += cantidad
                        else:
                            piezas[p.cmp_pie] = cantidad
                        db.mod_pre_mod_pie.insert(pre=self.presupuestoId,
                                               pre_mod=kit['id'],
                                               pie=p.cmp_pie,
                                               formula=p.formula,
                                               cantidad=cantidad)
        db(db.pre_pie.pre == self.presupuestoId).delete()
        for k,v in piezas.items():
            db.pre_pie.insert(pre =self.presupuestoId,pieza=k,cantidad=v)
    def update_atr(self):
        db = self._db
        for k, v in self.atr.items():
            db(db.mod_pre_atr.update_or_insert(
                ((db.mod_pre_atr.pre == self.presupuestoId) & (db.mod_pre_atr.atr == k))), valor=v.value)
    def atr_sorted(self):
        """
        lista ordenada de atributos
        """
        a = sorted(self.atr, key=lambda x: (self.atr[x].name or '').upper())
        return a
    def select_kits_filtrados(self,subnave,cfg):
        pre=self.presupuestoId
        #tatr = db.mod_pre_atr  # atributos de config
        ttip = db.mod_cfg_mod
        query = (ttip.cfg == cfg)
        # filtro módulos de las configuraciones elegidas en naves con atributos del presupuesto
        # left a atributos del modulo y de la configuracion para  devolver todos los registros
        left = [db.mod_mod_atr.on((db.mod_mod_atr.mod == ttip.mod))]
                #tatr.on((tatr.atr == db.mod_mod_atr.atr) & (tatr.pre == pre) & (tatr.subnave==0) & (tatr.mod_tipo==ttip.mod_tipo) )]
                #db.mod_atr.on(db.mod_atr.id == db.mod_mod_atr.atr)]
        #como los valores no están guardados en tabla pre_atr, en esta consulta no selecciono valores, los buscaré en el dict self.atr
        #rows = db(query).select(ttip.mod, ttip.mod_tipo, ttip.formula, tatr.atr, tatr.valor, db.mod_mod_atr.valores,db.mod_atr.tipo, distinct=True, left=left, orderby=(ttip.mod, ttip.mod_tipo))
        rows = db(query).select(ttip.mod, ttip.mod_tipo, ttip.formula, db.mod_mod_atr.atr,db.mod_mod_atr.valores, distinct=True, left=left, orderby=(ttip.mod, ttip.mod_tipo))
        # buclea para comparar atributos
        mod = {}
        lista = []
        excluye = False
        for row in rows:
            mod0 = {'mod': row[ttip.mod], 'mod_tipo': row[ttip.mod_tipo], 'formula': row[ttip.formula]}
            atr=row.mod_mod_atr.atr
            if mod0 != mod and mod:
                if not excluye:
                    lista.append(mod)
                else:
                    excluye = False
            if row.mod_cfg_mod.mod==1226:
                pass
            if not excluye:  # si ya hay un atributo de valores no coincidentes ya no comparo hasta cambio de kit
                if atr and self.atr.get(atr):
                    if self.atr[atr].tipo == MOD_ATR_TIPO.valores and row.mod_mod_atr.valores:  # si hay coincidencia de atributos en pre y en modulo, proceso a ver si tienen valores comunes
                        idvalor=self.atr.get_value_context(atr,subnave,row[ttip.mod_tipo]).idvalue
                        if idvalor:
                            if idvalor  not in row.mod_mod_atr.valores:
                                excluye = True
            mod = mod0
        if not excluye and mod:
            lista.append(mod)
        return lista
    def redondea_floats(self):
        for k, v in self.atr.items():
            for i in ('value', 'valores'):
                v[i] = redondea_si_float(v[i])
    def salva_atr(self):
        # guarda atributos calculados (solo los de una lista, TODO habrá que hacer esta lista automática!!!)
        # Pasa floats a Decimal 2 decimales

        sel = ((db.mod_pre_atr.pre == self.presupuestoId) & (db.mod_pre_atr.subnave == self.atr.subnave) & (
        db.mod_pre_atr.mod_tipo == self.atr.mod_tipo))
        # aqui poner la lilsta de atributos que deseemos guardar en base de datos, como aquellos que son argumentos en formulas de atributos secundarios
        lista = [ATRS._matriz_largo, ATRS._matriz_ancho, 156]
        # db(sel).update(tag=False)
        for k, v in self.atr.items():
            # formateo de valores de coma flotante
            if k in lista and v.tipo != MOD_ATR_TIPO.valores:
                db.mod_pre_atr.update_or_insert(sel & (db.mod_pre_atr.atr == k),
                                                subnave=self.atr.subnave, mod_tipo=self.atr.mod_tipo,
                                                pre=self.presupuestoId, atr=k, valor=v.value, tag=True, opcional=False)


                # db(sel & (db.mod_pre_atr.tag==False)).delete()

    """
Cálculo de canales.
Hay canales izq, derecha e intermedias. Dentro de estas con bajante, sin bajante y cumbrera, y esos 9 tipos se combinan en longitudes de 2, 2.5, 3, 4, 5 y 6 metros, con lo que hay 54 tipos de canal
Doble pendiente. En cada línea de canal, se ha de incluir una de tipo cumbrera
Hay una varible que indica el Y de la posición de la cumbrera. Si hay naves que están fuera de esa posicion, se tomarán como pendiente única.
Accesorios:
Caso pendiente única. Por cada líena hay que añadir un kit de tapa y un kit de bajante extremo
Pendiente doble: por cada linea se añade 2 kits de bajante extremo. Las líneas que no llevan cumbrera llevan tapa y bajante igual que simple pendiente

PROCESO.
-Recorrer todos los tuneles y modulos para calcular los tramos mixtos que cargandolos en una lista de pares (subtrramos)
trmcan[(tipo,uds),..] donde tipo es izq,derecha, medio., uds=modulos (1=sep_vanos)
-Después por canda línea, recorrer la lista calculada de subtramos,
Por cada subtramo si está en posy de cumbrera, se le calcula un modulo de longtitud mínima. Resto se calcula las logitudes necesarias máximas.
Cada modulo calculado se creaun objeto clase canal y se asigna a atributos canal izq o der del modulo en el matriz genral en los nodos correspondientes.
Un objecto canal de 6 metros se asignará a tres modulos de la matriz, p.e.
Tambíen se le asigna el atributo canalextremo norte y sur (tapa o bajante) en caso de fin/principio de tunel o null si está en medio


Bajantes intermedias. Hay una variable que indica la separacion minima entre bajantes intermedias (30 m defecto). Se tomará cada tramo (todos los de pendiente única y los dos tramos de cada pendiene
doble como tramos separados en los que se sustiuye una canal bajante intermedia. En los de doble pendiente, normalmente serán de 2*sep, ya que la cumbrerá se habrá tomado de long=sep en caso de no ser
multiplo de sep*2 todo el tramo doble. En los tramos de pendiente unica no multiplos de sep*2, se tomará la canal bajante intermedia de long=sep.
test
"""
