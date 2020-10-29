#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Clases de variables constantes que deben declararse antes de de todo para todo el proyecto, antes incluso que db.py"""
from gluon.storage import Storage

FORMULAS_PREFIJO = '@'
IDRAIZ_MOD_TIPO = 1
# FORMULAS_SEPARADORES='{}'
# FORMULAS_REGEXPR="\{[^\{]*\}"
FORMULAS_REGEXPR = "@([a-zA-Z0-9_]+)"


class InverAtr(Storage):
    def __init__(self, value, key=None, name=None, tipo='F',id=None,idvalue=None):
        self.key = key
        self.name = name
        self.value = value
        self.tipo = tipo
        self.id=id
        self.idvalue=idvalue
    def __repr__(self):
        return ' %{0}={1}'.format(self.name,self.value)

    def __value__(self):
        return self.value


class MOD_ATR_TIPO():
    formula = 'F'  # escalar
    vector = 'N'  # vector
    valores = 'V'
    diccionario = 'D'

    @classmethod
    def getitems(self):
        return {self.formula: 'Escalar', self.vector: 'Vector', self.valores: 'Valores discretos',
                self.diccionario: 'Diccionario'}



ATRS = Storage(
    nave_ancho=84,
    nave_long=113,
    nave_posy=114,
    separacion_vanos=103,
    _nod_esq_ext_izq=115,
    _nod_esq_ext_der=123,
    _nod_esq_int_izq=127,
    _nod_esq_int_der=132,
    _nod_lat_sab_izq=133,
    _nod_lat_sab_der=135,
    _nod_lat_din_izq=134,
    _nod_lat_din_der=136,
    _nod_frn_ali=137,
    _nod_int_sab=138,
    _nod_int_din=139,
    _lin_sable=140,
    _matriz_largo=141,
    _matriz_ancho=142,
    _ntuneles=143,
    _nmodulos=144,
    _seg_frn_ext=145,  # dict
    _seg_frn_med=146,  # dict
    _seg_lon_ext=147,
    _seg_lon_med=148,
    _seg_tra_sab_med=149,
    _seg_tra_sab_lat=150,
    _seg_tra_din_med=151,
    _seg_tra_din_lat=153,
    _trm_cor_lat_izq=154,  # list
    _trm_cor_lat_der=155,  # list
    _trm_cor_frn=156,  # dict[list]
    _trm_can=157,  # list
    pendiente=166,
    bajantes=167,
    pospte=168,
    _canales=169,
    lon_can_sbj=173,
    lon_can_cbj=174,
    lon_can_cum=175,)  # dict de dict
"""
    _trm_can_ext_der=158,#list
    _trm_can_med=159, #list
    _trx_can_ini_izq=160,#list
    _trx_can_ini_der=161,#list
    _trx_can_med=162,#list
    _trx_can_fin_izq=163,#list
    _trx_can_fin_der=164,#list
    """


class MOD_CMP_TIPO():
    pieza = 'P'
    modulo = 'M'
    ninguno='0'
    @classmethod
    def getitems(self,zero=False):
        dc={self.pieza: 'Pieza', self.modulo: 'Kit'}
        if zero:
            dc[self.ninguno]='-ninguno-'
        return dc



class ATR_ESPECIAL():
    PZORIGEN = 112
    GRUPO_PRIMARIO=5
    GRUPO_SECUNDARIO = 8
    GRUPO_SALIDA = 9

class TipoPendiente():
    SN = 0
    NS = 1
    doble=2
