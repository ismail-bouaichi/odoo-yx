# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DeliveryShipmentPackage(models.Model):
    _name = 'delivery.shipment.package'
    _description = 'Shipment Package'
    _order = 'sequence, id'

    shipment_id = fields.Many2one(
        'delivery.shipment',
        string='Shipment',
        required=True,
        ondelete='cascade',
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    
    name = fields.Char(
        string='Package Reference',
        compute='_compute_name',
        store=True,
    )
    
    gab = fields.Char(
        string='GAB',
        help="Barcode number (e.g., LI000006399MA)",
        required=True,
    )
    
    cab1 = fields.Char(
        string='CAB1',
        compute='_compute_cab1',
        store=True,
        help="Code 39 barcode format: *GAB*",
    )
    
    @api.depends('gab')
    def _compute_cab1(self):
        for package in self:
            if package.gab:
                package.cab1 = f"*{package.gab}*"
            else:
                package.cab1 = False

    @api.depends('shipment_id.name', 'sequence')
    def _compute_name(self):
        for package in self:
            if package.shipment_id and package.gab:
                package.name = package.gab
            else:
                package.name = f"Package {package.sequence}"
