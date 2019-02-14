# -*- coding: utf-8 -*-
{
    'name': 'Sale Purchase Intercompany',
    'version': '0.1',
    'license': 'AGPL-3',
    'category': 'Z Modules',
    'description': """
This module adds the ability to generate sales and purchase orders automatically.
=================================================================================
Example: Company A generates a purchase order from Company B. On Company B you do not need to manually create the sales order. Just click a button to create an inter company order form.

Company B generates a sales order to company A. On company A the purchase order is created automatically.

    """,
    'author': 'Zuher ELMAS',
    'depends': [
        'account',
        'sale',
        'purchase',
        'stock',
        'pricelist_extend'
    ],
    'data': [
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'wizard/launch_sale_purchase_wizard_views.xml',

        'security/ir.model.access.csv',

    ],
    'installable': True,
}
