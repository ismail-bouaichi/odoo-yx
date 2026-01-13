# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipment_id = fields.Many2one(
        'delivery.shipment',
        string='Shipment',
        copy=False,
    )
    
    can_create_shipment = fields.Boolean(
        string='Can Create Shipment',
        compute='_compute_can_create_shipment',
    )

    @api.depends('state', 'picking_type_code', 'delivery_company_id', 'shipment_id')
    def _compute_can_create_shipment(self):
        for picking in self:
            picking.can_create_shipment = (
                picking.state == 'done' and
                picking.picking_type_code == 'outgoing' and
                picking.delivery_company_id and
                not picking.shipment_id
            )

    def _get_sale_order(self):
        """Get the sale order linked to this picking."""
        self.ensure_one()
        if self.group_id and hasattr(self.group_id, 'sale_id') and self.group_id.sale_id:
            return self.group_id.sale_id
        if self.origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
            if sale_order:
                return sale_order
        return False

    def _create_shipment(self):
        """Create a shipment record for this delivery order."""
        self.ensure_one()
        if self.shipment_id:
            return self.shipment_id
            
        sale_order = self._get_sale_order()
        
        shipment_vals = {
            'picking_id': self.id,
            'delivery_company_id': self.delivery_company_id.id,
            'nbr_colis': sale_order.nbr_colis if sale_order else 1,
            'shipping_payment_method': sale_order.shipping_payment_method if sale_order else 'cash',
            'transport_nature': sale_order.transport_nature if sale_order else 'standard',
        }
        
        shipment = self.env['delivery.shipment'].create(shipment_vals)
        self.shipment_id = shipment
        return shipment

    def action_create_shipment(self):
        """Create a shipment from the delivery order (button action)."""
        self.ensure_one()
        if not self.shipment_id:
            self._create_shipment()

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
