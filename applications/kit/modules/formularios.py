#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
import datetime, random,cStringIO
import os, glob
from gluon.contrib.appconfig import AppConfig

class varsForm(object):
    vars={}
    def _decodifica(self,v):
        if v:   
            try:
                r=v.to_unicode()
            except:
                try:
                    r= v.decode('latin1').encode('utf8')
                except:
                    r=v
            return r.replace('(','').replace(')','')
        else:
            r=None
    def __init__(self, archivo):
        from gluon.contrib import pdfrw
        template = pdfrw.PdfReader(archivo)
        self.vars={} #parse fields
        for page in template.Root.Pages.Kids:
            for field in page.Annots:
                if field.T: #etiqueta de campo
                    label = self._decodifica(field.T)
                    valor=field.V
                    if valor:
                        valor=self._decodifica(valor) #valor
                    des=self._decodifica(field.TU) #descripcion
                    self.vars[label]={0:valor,1:des}
    def getBoolean(self,dato):
        if self.vars.get(dato):
            if self.vars.get(dato)[0] in ('/Sí','/Yes','/On'):
                return True
            elif self.vars.get(dato)[0] in ('/No','/Off'):
                return False
        else:
            return None
    def getVal(self,tag):
        if self.vars.get(tag):
            return self.vars[tag][0]
        else:
            return None
    def getDes(self,tag):
        if self.vars.get(tag):
            return self.vars[tag][1]
        else:
            return None

def verifica_formulario_recepcion(archivo):
    vf=varsForm(archivo)
    err=''
    cabs={}
    obligados_linea={'T':('Lon','LonV','Esp','EspV','Per'),'C':('Med','MedV','Lon','LonV','Esp','EspV'),'F':('Med','MedV','Esp','EspV','Ext','ExtV')}
    obligados_cab={'T':('ELon','EEsp'),'C':('EMed','EEsp','ELon'),'F':('EMed','EEsp','EExt')}
    opcionales_lin={'Rec':('RecV%s','ERec')}
    if vf.vars:
        for k in vf.vars:
            v=vf.getVal(k)
            if k.startswith('BIEN'):
                mal='MAL%s'%k[4:]
                if v and vf.getBoolean(mal):
                    err+='Casillas %s y %s activadas a la vez\n'%(k,mal)
            if v:
                if 'Car' in k[1:4]:
                    fila=k[4:]
                    tipo=k[0]
                    cabs[tipo]=True
                    if obligados_linea.has_key(tipo): #chequeo obligados en la línea
                        for i in obligados_linea[tipo]:
                            label=tipo+i+fila
                            if not vf.getVal(label):
                                if vf.getDes(label):
                                    err+='Falta %s en %s\n'%(vf.getDes(label),v)
                                else:
                                    err+='Falta dato %s en %s\n'%(i,v)
                    for k,v0 in opcionales_lin.items():
                        if vf.getVal(tipo+k+fila):
                            for i in v0:
                                dato= vf.getVal((tipo+i)%fila) if '%' in i else vf.getVal(tipo+i)
                                if not dato:
                                    if vf.getDes(label):
                                        err+='Falta %s en %s\n'%(vf.getDes(label),v)
                                    else:
                                        err+='Falta dato %s en %s\n'%(v0,v)
        for tipo in cabs:
            if obligados_cab.has_key(tipo): #chequeo equipos
                for i in obligados_cab[tipo]:
                    label=tipo+i
                    if not vf.getVal(label):
                        if vf.getDes(label):
                            err+='Falta %s\n'%vf.getDes(label)
                        else:
                            err+='Falta dato equipo %s\n'%(label)
        if not(vf.getBoolean('BIEN')) and not(vf.getBoolean('MAL')):
            err+=u'Falta Resumen de Inspección (Apto. 5)\n'
    else:
        err='No hay campos en el formulario'
    return err

def tipopagina_por_codigoproducto(codigo):
    #paginas={'T':2,'C':3,'F':4} #paginas del pdf
    tipo=codigo[0]
    if tipo in 'HL': #chapas/pletinas
        return 'C',3
    elif tipo=='F': #Flejes
        return 'F',4
    elif tipo in "DRCIJIZOMAUVP": #perfiles y tubos
        return 'T',2
    else:
        return None,None

def genera_variables_formulario(db,idformulario,pedido,selineas=None):
    #busca en formulario campos las variables que necesitamos para enviarselas al terminal
    campos=[]
    pedidos=db((db.pedpro.pedido.belongs(pedido)) & (db.pedpro.id.belongs(selineas))).select(db.pedpro.id,db.pedpro.proveedor,db.pedpro.producto,db.pedpro.codigo,orderby=db.pedpro.codigo)
    pags=[1] #lista de paginas a generar
    if pedidos: #escruto lineas de pedido para ver qué paginas del formulario necestio
        for row in pedidos:
            t,p=tipopagina_por_codigoproducto(row.codigo)
            row.update(pagina=p)
            if p:
                if not p in pags:
                    pags.append(p)
    #añade campos de cabecera de las paginas
    cabecera=db((db.formularioscampos.idformulario==idformulario) & (db.formularioscampos.linea==0)).select(orderby=(db.formularioscampos.pagina,db.formularioscampos.linea,db.formularioscampos.columna))
    if cabecera:
        for c in cabecera.as_list():
            if c['pagina'] in pags:
                campos.append(c)
    #añade campos de lineas generando tantos como lineas de pedido requeridas
    lineas=db((db.formularioscampos.idformulario==idformulario) & (db.formularioscampos.linea==1)).select(orderby=(db.formularioscampos.pagina,db.formularioscampos.linea,db.formularioscampos.columna))
    l=0
    if pedidos and lineas:
        for row in pedidos:
            l+=1
            for c in lineas.as_list():
                if c['pagina']==row['pagina']:
                    m=dict(**c)
                    if '*' in m['clave']:
                        m['clave']=m['clave'].replace('*',str(l))
                        m['linea']=l
                    if m['valorpredeterminado']:
                        if '%(' in m['valorpredeterminado']:
                            m['valorpredeterminado']=m['valorpredeterminado'] % row
                    campos.append(m)
    campos.sort(key=lambda k: k['pagina'])
    return campos

def genera_formulario_recepcion(db,dict_fields,outfile):
    from shutil import copyfile
    myconf = AppConfig(reload=False)
    dict_fields['FECHA']=datetime.datetime.strftime(current.request.now,'%d/%m/%Y')
    for k,v in dict_fields.items():
        dict_fields[k]=v.decode('utf8')
    pdffile=os.path.join(current.request.folder,myconf.get('paths.forms'), myconf.get('paths.form_recepcion'))
    pages_to_keep=dict_fields.get("paginas")
    temp= genera_formulario(pdffile,dict_fields,pages=pages_to_keep,devuelve_stream=False)
    copyfile(temp,outfile)

def genera_formulario_recepcion_old(db,pedido,albaran,operario,selineas=None):
    from shutil import copyfile
    myconf = AppConfig(reload=False)
    rows=db((db.pedpro.pedido==pedido) & (db.pedpro.idestado.belongs((802,803)))).select(db.pedpro.id,db.pedpro.proveedor,db.pedpro.producto,db.pedpro.codigo)
    if rows:
        fecha=datetime.datetime.strftime(current.request.now,'%d/%m/%Y')
        dict_fields=dict(ALBARAN=albaran,
                     PEDIDO=pedido,
                     FIRMADO=operario,
                     PROVEEDOR=rows[0].proveedor,
                     FECHA=fecha)
        lineas={'T':[],'C':[],'F':[]} #tubos,chapas,flejes
        paginas={'T':2,'C':3,'F':4} #paginas del pdf
        pages_to_keep = '1 '
        for row in rows:
            if (str(row.id) in selineas) or (not selineas):
                t,p=tipopagina_por_codigoproducto(row.codigo)
                if t:
                    lineas[t]+=[row.producto]
                    if not p in pages_to_keep:
                        pages_to_keep += '%s '%p
        dif=random.randrange(10000)
        sufijo=''
        for k,v in lineas.items():
            if v:
                for i in range(0,len(v)):
                    dict_fields['%sCar%s'%(k,i+1)]=v[i]
                sufijo+=k
        #no use pages, ya que muPDF si quito paginas con PDFTK no visualiza bien
        #convierto a utf8 porque fdfgen convierte utf16be y si le llegan en latin1 u otra cosa , casca
        for k,v in dict_fields.items():
            dict_fields[k]=v.decode('utf8')
        #dejamos el PDF con solo las paginas interesadas
        #pages_to_keep = [1, 2, 10] # page numbering starts from 0
        pdffile=os.path.join(current.request.folder,myconf.get('paths.forms'), myconf.get('paths.form_recepcion'))
        if len(sufijo)==22:
            pdffile=pdffile.replace('.pdf',sufijo+'.pdf')
            pdffile=pdffile.replace('.PDF',sufijo+'.PDF')
        return genera_formulario(pdffile,dict_fields,dif,pages=pages_to_keep)
    else:
        return dict(resp={'errors':T('Register not found')})
def touch_dir(directory):
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)

def genera_formulario(pdffile,dict_fields,dif=None,pages=None,devuelve_stream=True):
    #si devuelve_stream=False devuevel la ruta del archivo generado
    from gluon.contrib.fdfgen import forge_fdf
    myconf = AppConfig(reload=False)
    fields=[(i,dict_fields[i]) for i in dict_fields]
    fdf = forge_fdf("",fields,[],[],[])
    if not dif:
        dif=random.randrange(10000)
    infile = os.path.join(current.request.folder, 'temp', 'data%s.fdf'%dif)
    outfile= os.path.join(current.request.folder, 'temp', 'out%s.pdf'%dif)
    touch_dir(os.path.join(current.request.folder,'temp'))
    fdf_file = open(infile,"wb")
    fdf_file.write(fdf)
    fdf_file.flush()
    fdf_file.close()
    comando=  myconf.get('paths.pdftk')+' "%s" fill_form "%s" output "%s" '%(pdffile,infile,outfile)
    s=os.popen(comando)
    s.flush()
    res=s.read()
    s.close()
    #al eliminar paginasl mupdf pierde campos del formulario
    if pages:
        outfile2= os.path.join(current.request.folder, 'private', 'outp%s.pdf'%dif)
        comando=  myconf.get('paths.pdftk')+' "%s" cat %s output "%s" '%(outfile,pages,outfile2)
        s=os.popen(comando)
        s.flush()
        res=s.read()
        s.close()
        outfile=outfile2
    #acuerdate de la opcion flatten para cerrarlo al recibir el formulario rellenado
    if devuelve_stream:
        try:
            data = open(outfile,"rb").read()
            current.response.headers['Content-Type']='application/pdf'
            return current.response.stream(cStringIO.StringIO(data))
        except:
            raise HTTP(400,res)
    else:
        return outfile

def descarga_plano(codigo):
    myconf = AppConfig(reload=False)
    ruta=  os.path.join(myconf.get('paths.docplanos'), codigo)
    items=os.listdir(ruta)
    for item in items:
        if item.upper().endswith('.PDF'):
            outfile= os.path.join(ruta,item)
            data = open(outfile,"rb").read()
            current.response.headers['Content-Type']='application/pdf'
            return current.response.stream(cStringIO.StringIO(data))
