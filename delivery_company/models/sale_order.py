# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
        help="Delivery company for shipping this order",
    )
    
    # Shipping details fields
    nbr_colis = fields.Integer(
        string='Number of Packages',
        default=1,
        help="Number of packages for this shipment",
    )
    shipping_payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash (Espèce)'),
        ('cheque', 'Cheque'),
        ('effet', 'Effet'),
    ], string='Payment Method', default='cash',
       help="Payment method for the delivery")
    
    transport_nature = fields.Selection([
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('domicile', 'Home Delivery (À Domicile)'),
    ], string='Transport Nature', default='standard',
       help="Nature of transportation required")

    @api.onchange('partner_id')
    def _onchange_partner_delivery_company(self):
        """Auto-fill delivery company from customer."""
        if self.partner_id and self.partner_id.delivery_company_id:
            self.delivery_company_id = self.partner_id.delivery_company_id
            if self.delivery_company_id.default_transport_nature:
                self.transport_nature = self.delivery_company_id.default_transport_nature

    @api.onchange('delivery_company_id')
    def _onchange_delivery_company_transport(self):
        """Auto-fill transport nature from delivery company."""
        if self.delivery_company_id and self.delivery_company_id.default_transport_nature:
            self.transport_nature = self.delivery_company_id.default_transport_nature

    def _prepare_invoice(self):
        """Pass delivery company and payment method to invoice."""
        vals = super()._prepare_invoice()
        vals['delivery_company_id'] = self.delivery_company_id.id
        vals['shipping_payment_method'] = self.shipping_payment_method
        return vals
