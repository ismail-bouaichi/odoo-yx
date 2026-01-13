# -*- coding: utf-8 -*-
{
    'name': 'Delivery Shipment',
    'version': '1.3',
    'summary': 'Shipment Management with Barcode Generation',
    'description': """
        Manage shipments for delivery orders.
        - Auto-create shipment when OUT is validated
        - Generate barcodes (GAB, CAB1, MS Destinataire)
        - Support multiple packages per shipment
        - Track shipment status
        - Change delivery company if needed
        - Export to Excel for Barid (Amana)
        - Print shipment labels (Amana format)
    """,
    'category': 'Operations/Inventory',
    'author': 'Odoo Developer',
    'depends': ['delivery_company', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/delivery_shipment_package_views.xml',
        'views/delivery_shipment_views.xml',
        'wizard/export_wizard_views.xml',
        'report/shipment_label_amana_report.xml',
        'report/shipment_label_generic_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
