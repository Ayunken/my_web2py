# -*- coding: utf-8 -*-
from gluon import current
from gluon.admin import *
from datetime import date
def inicio():
    current.logger.debug("Inicio Sistema")
def limpieza():
    if len(request.args)>0:
        app=request.args[0]
    else:
        app='Modulero'
    current.logger.debug("limpieza %s"%app)
    d=app_cleanup(app,current.request)
    if d:
        current.logger.debug("limpieza correcta")
    else:
        current.logger.debug("limpieza ERROR")
