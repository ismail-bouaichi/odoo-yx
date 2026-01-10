# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
        help="Delivery company for this shipment",
    )
    
    # Shipping details fields (copied from Sale Order)
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
    ], string='Transport Nature',
       help="Nature of transportation required")

    def _get_sale_order(self):
        """Get the sale order linked to this picking."""
        self.ensure_one()
        # Try direct link first
        if self.sale_id:
            return self.sale_id
        # Try via procurement group
        if self.group_id and self.group_id.sale_id:
            return self.group_id.sale_id
        # Try via origin field (SO name)
        if self.origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
            if sale_order:
                return sale_order
        return False

    def write(self, vals):
        """When delivery company or payment method changes on OUT, update related documents of the day."""
        res = super().write(vals)
        
        # Skip propagation if called from create or internal propagation
        if self.env.context.get('skip_propagation'):
            return res
        
        # Only propagate if delivery_company_id or shipping_payment_method changed on outgoing picking
        if 'delivery_company_id' in vals or 'shipping_payment_method' in vals:
            for picking in self:
                if picking.picking_type_code == 'outgoing':
                    picking._propagate_shipping_changes_to_related_docs()
        return res

    def _propagate_shipping_changes_to_related_docs(self):
        """Propagate delivery company and payment method changes to related documents created today."""
        self.ensure_one()
        today = date.today()
        
        # Get related sale order
        sale_order = self._get_sale_order()
        if sale_order and sale_order.date_order.date() == today:
            sale_order.write({
                'delivery_company_id': self.delivery_company_id.id,
                'shipping_payment_method': self.shipping_payment_method,
            })
        
        # Get related pickings (Pick operations) created today
        if self.group_id:
            related_pickings = self.env['stock.picking'].search([
                ('group_id', '=', self.group_id.id),
                ('id', '!=', self.id),
                ('create_date', '>=', fields.Datetime.to_string(today)),
            ])
            for pick in related_pickings:
                pick.with_context(skip_propagation=True).write({
                    'delivery_company_id': self.delivery_company_id.id,
                    'shipping_payment_method': self.shipping_payment_method,
                })
        
        # Get related invoices in draft (not yet confirmed)
        if sale_order:
            invoices = sale_order.invoice_ids.filtered(
                lambda inv: inv.state == 'draft'
            )
            invoices.write({
                'delivery_company_id': self.delivery_company_id.id,
                'shipping_payment_method': self.shipping_payment_method,
            })

    @api.model_create_multi
    def create(self, vals_list):
        """Fill shipping details from sale order on creation."""
        pickings = super().create(vals_list)
        for picking in pickings:
            sale_order = picking._get_sale_order()
            if sale_order:
                # Always copy shipping details from SO if not already set in vals
                update_vals = {}
                if not picking.delivery_company_id and sale_order.delivery_company_id:
                    update_vals['delivery_company_id'] = sale_order.delivery_company_id.id
                if not picking.nbr_colis or picking.nbr_colis == 1:
                    update_vals['nbr_colis'] = sale_order.nbr_colis or 1
                if not picking.shipping_payment_method and sale_order.shipping_payment_method:
                    update_vals['shipping_payment_method'] = sale_order.shipping_payment_method
                if not picking.transport_nature and sale_order.transport_nature:
                    update_vals['transport_nature'] = sale_order.transport_nature
                if update_vals:
                    picking.with_context(skip_propagation=True).write(update_vals)
        return pickings

    def _action_done(self):
        """Propagate delivery company and shipping details to next pickings in the chain when validated."""
        res = super()._action_done()
        for picking in self:
            # Find next pickings in the chain through move destinations
            next_pickings = picking.move_ids.move_dest_ids.picking_id.filtered(lambda p: p)
            for next_picking in next_pickings:
                update_vals = {}
                if not next_picking.delivery_company_id and picking.delivery_company_id:
                    update_vals['delivery_company_id'] = picking.delivery_company_id.id
                if (not next_picking.nbr_colis or next_picking.nbr_colis == 1) and picking.nbr_colis:
                    update_vals['nbr_colis'] = picking.nbr_colis
                if not next_picking.shipping_payment_method and picking.shipping_payment_method:
                    update_vals['shipping_payment_method'] = picking.shipping_payment_method
                if not next_picking.transport_nature and picking.transport_nature:
                    update_vals['transport_nature'] = picking.transport_nature
                if update_vals:
                    next_picking.write(update_vals)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """Pass delivery company and shipping details to pickings when confirming sale order."""
        res = super()._action_confirm()
        for order in self:
            for picking in order.picking_ids:
                update_vals = {}
                if not picking.delivery_company_id and order.delivery_company_id:
                    update_vals['delivery_company_id'] = order.delivery_company_id.id
                if (not picking.nbr_colis or picking.nbr_colis == 1) and order.nbr_colis:
                    update_vals['nbr_colis'] = order.nbr_colis
                if not picking.shipping_payment_method and order.shipping_payment_method:
                    update_vals['shipping_payment_method'] = order.shipping_payment_method
                if not picking.transport_nature and order.transport_nature:
                    update_vals['transport_nature'] = order.transport_nature
                if update_vals:
                    picking.write(update_vals)
        return res
