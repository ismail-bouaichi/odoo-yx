# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
        help="Delivery company for this invoice",
        copy=False,
    )
    
    shipping_payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash (Espèce)'),
        ('cheque', 'Cheque'),
        ('effet', 'Effet'),
    ], string='Shipping Payment Method',
       help="Payment method for the delivery",
       copy=False)

    @api.onchange('partner_id')
    def _onchange_partner_delivery_company(self):
        """Auto-fill delivery company from customer only if not already set."""
        if self.partner_id and self.partner_id.delivery_company_id and not self.delivery_company_id:
            self.delivery_company_id = self.partner_id.delivery_company_id
        elif not self.partner_id:
            self.delivery_company_id = False
