{
    'name': 'Delivery Company',
    'version': '1.9',
    'summary': 'Manage Delivery Company Configurations',
    'description': """
        This module allows you to manage delivery company credentials and API details.
        Supports Barid Al-Maghrib (Amana) and other delivery providers.
    """,
    'category': 'Operations/Inventory',
    'author': 'Odoo Developer',
    'depends': ['base', 'sale', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/delivery_company_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'reports/report_templates.xml',
    ],
    'post_init_hook': '_assign_default_delivery_company',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
