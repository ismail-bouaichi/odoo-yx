# -*- coding: utf-8 -*-
from . import models
from . import services


def _assign_default_delivery_company(env):
    """
    Post-init hook: Assign default Barid delivery company to existing customers
    who don't have one assigned. Uses the first active Barid provider found.
    """
    default_company = env['delivery.company'].search(
        [('provider_type', '=', 'barid'), ('active', '=', True)],
        limit=1
    )
    
    if default_company:
        customers_without_delivery = env['res.partner'].search([
            ('delivery_company_id', '=', False),
            ('customer_rank', '>', 0)
        ])
        if customers_without_delivery:
            customers_without_delivery.write({
                'delivery_company_id': default_company.id
            })
