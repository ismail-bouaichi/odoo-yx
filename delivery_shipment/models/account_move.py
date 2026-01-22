# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    shipment_id = fields.Many2one(
        'delivery.shipment',
        string='Shipment',
        copy=False,
    )
    
    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
    )

    def _get_sale_order(self):
        """Get the sale order linked to this invoice."""
        self.ensure_one()
        # Try to get from invoice origin
        if self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
            if sale_order:
                return sale_order
        # Try from invoice lines
        for line in self.invoice_line_ids:
            if line.sale_line_ids:
                return line.sale_line_ids[0].order_id
        return False

    def _get_delivery_picking(self):
        """Get the delivery picking linked to this invoice."""
        self.ensure_one()
        sale_order = self._get_sale_order()
        if sale_order:
            # Get done delivery pickings
            pickings = sale_order.picking_ids.filtered(
                lambda p: p.picking_type_code == 'outgoing' and p.state == 'done'
            )
            if pickings:
                return pickings[0]
        return False

    def _create_shipment(self):
        """Create a shipment record for this invoice."""
        self.ensure_one()
        if self.shipment_id:
            return self.shipment_id
        
        # Get the delivery picking
        picking = self._get_delivery_picking()
        if not picking:
            raise UserError(_("No delivery order found for this invoice. Please ensure the delivery is done first."))
        
        # Check if picking already has a shipment
        if picking.shipment_id:
            self.shipment_id = picking.shipment_id
            return picking.shipment_id
        
        if not self.delivery_company_id:
            raise UserError(_("Please select a Delivery Company first."))
        
        sale_order = self._get_sale_order()
        
        shipment_vals = {
            'picking_id': picking.id,
            'delivery_company_id': self.delivery_company_id.id,
            'nbr_colis': sale_order.nbr_colis if sale_order and hasattr(sale_order, 'nbr_colis') else 1,
        }
        
        shipment = self.env['delivery.shipment'].create(shipment_vals)
        self.shipment_id = shipment
        picking.shipment_id = shipment
        return shipment

    def action_create_shipment(self):
        """Create a shipment from the invoice (button action)."""
        self.ensure_one()
        if not self.shipment_id:
            self._create_shipment()
        return self.action_open_shipment()

    def action_open_shipment(self):
        """Open the related shipment."""
        self.ensure_one()
        if not self.shipment_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shipment'),
            'res_model': 'delivery.shipment',
            'res_id': self.shipment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
