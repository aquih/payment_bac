# -*- coding: utf-8 -*-

{
    'name': 'BAC Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: BAC Implementation',
    'version': '1.0',
    'description': """BAC Payment Acquirer""",
    'author': 'aquíH',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_bac_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
