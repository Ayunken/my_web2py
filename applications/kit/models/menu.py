# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# ----------------------------------------------------------------------------------------------------------------------
# Customize your APP title, subtitle and menus here
# ----------------------------------------------------------------------------------------------------------------------

response.logo = A(B('INVERCA'), XML('&trade;&nbsp;'),
                  _class="navbar-brand", _href="http://www.web2py.com/",
                  _id="web2py-logo")
response.title = request.application.replace('_', ' ').title()
response.subtitle = ''


#response.files.append(URL(r=request,c='static/ui/js',f='jquery-ui.widget.js'))
#response.files.append(URL(r=request,c='static/ui/multiselect',f='jquery.multiselect.min.js'))
#response.files.append(URL(r=request,c='statics',f='test.js'))
# ----------------------------------------------------------------------------------------------------------------------
# read more at http://dev.w3.org/html5/markup/meta.name.html
# ----------------------------------------------------------------------------------------------------------------------
response.meta.author = myconf.get('app.author')
response.meta.description = myconf.get('app.description')
response.meta.keywords = myconf.get('app.keywords')
response.meta.generator = myconf.get('app.generator')

# ----------------------------------------------------------------------------------------------------------------------
# your http://google.com/analytics id
# ----------------------------------------------------------------------------------------------------------------------
response.google_analytics_id = None

# ----------------------------------------------------------------------------------------------------------------------
# this is the main application menu add/remove items as required
# ----------------------------------------------------------------------------------------------------------------------

response.menu = [
    (T('Home'), False, URL('default', 'index'), [])
]
DEVELOPMENT_MENU = True


# ----------------------------------------------------------------------------------------------------------------------
# custom menu
# ----------------------------------------------------------------------------------------------------------------------

def _mymenu():
    if auth.user:
        response.menu+=[
            (T('Tablas'), False, None, [
               (T('Tipos de Kits'),False,URL(c='mod',f='mod_tipos2')),
               (T('Piezas'),False,URL(c='mod',f='piezas')),
               (T('Kits'),False,URL(c='mod',f='grid_mod')),
               (T('Kits por Ubicacion'),False,URL(c='mod',f='mod_tipos')),
               (T('Configuraciones'),False,URL(c='cfg',f='grid_cfg')),
               (T('Presupuestos'),False,URL(c='pre',f='grid_pre')),
               (T('Reglas Modificación'),False,URL(c='mod',f='grid_mod_rul'))
            ]),
            (T('Auxiliares'), False, None, [
                        (T('Unidades'),False,URL(c='tablas',f='crud',vars=dict(table='mod_um')),[]),
                        (T('Atributos'),False,URL(c='tablas',f='grid_mod_atr'),[]),
                        (T('Atributos por grupos'),False,URL(c='tablas',f='mod_grp_atr'),[]),
                        (T('Valores'),False,URL(c='tablas',f='crud',vars=dict(table='mod_val')),[]),
                        (T('Idiomas'),False,URL(c='tablas',f='crud',vars=dict(table='idiomas')),[]),
                        (T('Componentes-Kits'),False,URL(c='tablas',f='crud',vars=dict(table='mod_cmp')),[]),
                        (T('Atributos-Kits'),False,URL(c='tablas',f='crud',vars=dict(table='mod_mod_atr')),[])
                 ])
            ]
        if auth.has_membership(group_id=1) :
            response.menu+=[ (T('Admin'), False, None, [
             (T('Usuarios'),False,URL(c='tablas',f='crud',vars=dict(table='auth_user')),[]),
             (T('Membresía'),False,URL(c='tablas',f='crud',vars=dict(table='auth_membership')),[]),
             (T('Grupos'),False,URL(c='tablas',f='crud',vars=dict(table='auth_group')),[]),
            ])]
    if DEVELOPMENT_MENU:
        if auth.user:
             if auth.has_membership(group_id=1) :
                _()



# ----------------------------------------------------------------------------------------------------------------------
# provide shortcuts for development. remove in production
# ----------------------------------------------------------------------------------------------------------------------

def _():
    # ------------------------------------------------------------------------------------------------------------------
    # shortcuts
    # ------------------------------------------------------------------------------------------------------------------
    app = request.application
    ctr = request.controller
    # ------------------------------------------------------------------------------------------------------------------
    # useful links to internal and external resources
    # ------------------------------------------------------------------------------------------------------------------
    response.menu += [
        (T('My Sites'), False, URL('admin', 'default', 'site')),
        (T('This App'), False, '#', [
            (T('Design'), False, URL('admin', 'default', 'design/%s' % app)),
            LI(_class="divider"),
            (T('Controller'), False,
             URL(
                 'admin', 'default', 'edit/%s/controllers/%s.py' % (app, ctr))),
            (T('View'), False,
             URL(
                 'admin', 'default', 'edit/%s/views/%s' % (app, response.view))),
            (T('DB Model'), False,
             URL(
                 'admin', 'default', 'edit/%s/models/db.py' % app)),
            (T('Menu Model'), False,
             URL(
                 'admin', 'default', 'edit/%s/models/menu.py' % app)),
            (T('Config.ini'), False,
             URL(
                 'admin', 'default', 'edit/%s/private/appconfig.ini' % app)),
            (T('Layout'), False,
             URL(
                 'admin', 'default', 'edit/%s/views/layout.html' % app)),
            (T('Stylesheet'), False,
             URL(
                 'admin', 'default', 'edit/%s/static/css/web2py-bootstrap3.css' % app)),
            (T('Database'), False, URL(app, 'appadmin', 'index')),
            (T('Errors'), False, URL(
                'admin', 'default', 'errors/' + app)),
            (T('About'), False, URL(
                'admin', 'default', 'about/' + app)),
        ]),
        ('web2py.com', False, '#', [
            (T('Download'), False,
             'http://www.web2py.com/examples/default/download'),
            (T('Support'), False,
             'http://www.web2py.com/examples/default/support'),
            (T('Demo'), False, 'http://web2py.com/demo_admin'),
            (T('Quick Examples'), False,
             'http://web2py.com/examples/default/examples'),
            (T('FAQ'), False, 'http://web2py.com/AlterEgo'),
            (T('Videos'), False,
             'http://www.web2py.com/examples/default/videos/'),
            (T('Free Applications'),
             False, 'http://web2py.com/appliances'),
            (T('Plugins'), False, 'http://web2py.com/plugins'),
            (T('Recipes'), False, 'http://web2pyslices.com/'),
        ]),
        (T('Documentation'), False, '#', [
            (T('Online book'), False, 'http://www.web2py.com/book'),
            LI(_class="divider"),
            (T('Preface'), False,
             'http://www.web2py.com/book/default/chapter/00'),
            (T('Introduction'), False,
             'http://www.web2py.com/book/default/chapter/01'),
            (T('Python'), False,
             'http://www.web2py.com/book/default/chapter/02'),
            (T('Overview'), False,
             'http://www.web2py.com/book/default/chapter/03'),
            (T('The Core'), False,
             'http://www.web2py.com/book/default/chapter/04'),
            (T('The Views'), False,
             'http://www.web2py.com/book/default/chapter/05'),
            (T('Database'), False,
             'http://www.web2py.com/book/default/chapter/06'),
            (T('Forms and Validators'), False,
             'http://www.web2py.com/book/default/chapter/07'),
            (T('Email and SMS'), False,
             'http://www.web2py.com/book/default/chapter/08'),
            (T('Access Control'), False,
             'http://www.web2py.com/book/default/chapter/09'),
            (T('Services'), False,
             'http://www.web2py.com/book/default/chapter/10'),
            (T('Ajax Recipes'), False,
             'http://www.web2py.com/book/default/chapter/11'),
            (T('Components and Plugins'), False,
             'http://www.web2py.com/book/default/chapter/12'),
            (T('Deployment Recipes'), False,
             'http://www.web2py.com/book/default/chapter/13'),
            (T('Other Recipes'), False,
             'http://www.web2py.com/book/default/chapter/14'),
            (T('Helping web2py'), False,
             'http://www.web2py.com/book/default/chapter/15'),
            (T("Buy web2py's book"), False,
             'http://stores.lulu.com/web2py'),
        ]),
        (T('Community'), False, None, [
            (T('Groups'), False,
             'http://www.web2py.com/examples/default/usergroups'),
            (T('Twitter'), False, 'http://twitter.com/web2py'),
            (T('Live Chat'), False,
             'http://webchat.freenode.net/?channels=web2py'),
        ]),
    ]

_mymenu()


if "auth" in locals():
    auth.wikimenu()
