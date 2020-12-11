# -*- coding: utf-8 -*-

{
    'name': 'BAC Payment Acquirer',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: BAC Implementation',
    'version': '1.0',
    'description': """BAC Payment Acquirer""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_bac_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
