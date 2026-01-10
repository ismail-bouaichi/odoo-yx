# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """
    Assign default Barid delivery company to existing customers without one.
    This runs automatically when upgrading the module.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find default Barid company
    default_company = env['delivery.company'].search(
        [('provider_type', '=', 'barid'), ('active', '=', True)],
        limit=1
    )
    
    if default_company:
        # Find customers without delivery company
        customers = env['res.partner'].search([
            ('delivery_company_id', '=', False),
            ('customer_rank', '>', 0)
        ])
        
        if customers:
            customers.write({'delivery_company_id': default_company.id})
