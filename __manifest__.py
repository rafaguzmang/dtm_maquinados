
{
    'name': 'Maquinados',
    'version': '1.0',
    'description': 'Modulo para llevar los maquinados',
    'author': 'Author',
    'license': 'LGPL-3',
    'depends': ['dtm_odt'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/dtm_maquinados_view.xml',
        'views/dtm_maquinados_terminados_view.xml',
        'views/dtm_menu.xml',
    ],
    'installable': True,
    'auto_install': False
}
