# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DeliveryShipment(models.Model):
    _name = 'delivery.shipment'
    _description = 'Delivery Shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Shipment Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    
    picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        required=True,
        ondelete='cascade',
        domain="[('picking_type_code', '=', 'outgoing'), ('state', '=', 'done')]",
    )
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        compute='_compute_sale_order_id',
        store=True,
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='picking_id.partner_id',
        store=True,
    )
    
    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
        required=True,
        tracking=True,
    )
    
    is_barid = fields.Boolean(
        string='Is Barid',
        compute='_compute_is_barid',
        store=True,
    )
    
    # Reference for non-Barid companies
    reference = fields.Char(
        string='Reference',
        help="Shipment reference number for non-Barid companies (single package)",
        tracking=True,
        copy=False,
    )
    
    # Reference range for multiple packages (non-Barid)
    reference_from = fields.Char(
        string='Reference From',
        help="Starting reference number for multiple packages",
        tracking=True,
        copy=False,
    )
    
    reference_to = fields.Char(
        string='Reference To',
        help="Ending reference number (auto-calculated from Reference From + Nombre de Colis)",
        compute='_compute_reference_to',
        store=True,
        readonly=False,
    )
    
    reference_display = fields.Char(
        string='Reference Range',
        compute='_compute_reference_display',
    )
    
    has_multiple_packages = fields.Boolean(
        string='Has Multiple Packages',
        compute='_compute_has_multiple_packages',
    )
    
    # Shipping details
    nbr_colis = fields.Integer(
        string='Number of Packages',
        default=1,
        tracking=True,
    )
    
    shipping_payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash (Espèce)'),
        ('cheque', 'Cheque'),
        ('effet', 'Effet'),
    ], string='Payment Method',
       default='cash',
       tracking=True,
    )
    
    transport_nature = fields.Selection([
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('domicile', 'Home Delivery (À Domicile)'),
    ], string='Transport Nature',
       default='standard',
       tracking=True,
    )
    
    # Barcode fields
    gab = fields.Char(
        string='GAB',
        help="Barcode number (e.g., LI000006399MA)",
        tracking=True,
        copy=False,
    )
    
    cab1 = fields.Char(
        string='CAB1',
        compute='_compute_cab1',
        store=True,
        help="Computed as *GAB*",
    )
    
    ms_destinataire = fields.Char(
        string='MS Destinataire',
        compute='_compute_ms_destinataire',
        store=True,
        readonly=False,
        help="Customer phone number",
    )
    
    # VD - Valeur Déclarée (declared value for fragile/valuable items)
    vd = fields.Float(
        string='VD',
        help="Declared value if package contains fragile or valuable items",
        tracking=True,
    )
    
    # CRBT fields (Cash/Cheque on delivery)
    crbt_espece = fields.Float(
        string='CRBT Espèce',
        help="Cash amount to collect on delivery",
        tracking=True,
    )
    
    crbt_cheque = fields.Char(
        string='CRBT Chèque',
        help="Cheque number for payment on delivery",
        tracking=True,
    )
    
    # Label fields for Amana template
    weight = fields.Float(
        string='Weight (Kg)',
        help="Package weight in kilograms",
    )
    
    pod = fields.Char(
        string='POD',
        help="Product description",
    )
    
    is_fragile = fields.Boolean(
        string='Fragile',
        help="Check if package contains fragile items",
    )
    
    dimension_length = fields.Float(
        string='Length (cm)',
        help="Package length in centimeters",
    )
    
    dimension_width = fields.Float(
        string='Width (cm)',
        help="Package width in centimeters",
    )
    
    dimension_height = fields.Float(
        string='Height (cm)',
        help="Package height in centimeters",
    )
    
    code_point_relais = fields.Char(
        string='Code Point Relais',
        help="Relay point code for pickup",
    )
    
    supplier_code = fields.Char(
        string='Supplier Code',
        help="Supplier/Sender code",
    )
    
    # Package barcodes (for multiple packages)
    package_ids = fields.One2many(
        'delivery.shipment.package',
        'shipment_id',
        string='Packages',
    )
    
    # Summary fields for UI
    package_count = fields.Integer(
        string='Package Count',
        compute='_compute_package_summary',
    )
    
    gab_range = fields.Char(
        string='GAB Range',
        compute='_compute_package_summary',
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string='Status',
       default='draft',
       tracking=True,
    )
    
    # Additional info
    shipping_date = fields.Date(
        string='Shipping Date',
        default=fields.Date.today,
    )
    
    delivery_date = fields.Date(
        string='Delivery Date',
    )
    
    notes = fields.Text(
        string='Notes',
    )

    @api.depends('picking_id')
    def _compute_sale_order_id(self):
        """Get sale order from picking."""
        for shipment in self:
            if shipment.picking_id:
                if shipment.picking_id.group_id and hasattr(shipment.picking_id.group_id, 'sale_id'):
                    shipment.sale_order_id = shipment.picking_id.group_id.sale_id
                elif shipment.picking_id.origin:
                    sale_order = self.env['sale.order'].search(
                        [('name', '=', shipment.picking_id.origin)], limit=1
                    )
                    shipment.sale_order_id = sale_order
                else:
                    shipment.sale_order_id = False
            else:
                shipment.sale_order_id = False

    @api.depends('delivery_company_id', 'delivery_company_id.provider_type')
    def _compute_is_barid(self):
        for shipment in self:
            shipment.is_barid = shipment.delivery_company_id.provider_type == 'barid'

    @api.depends('nbr_colis')
    def _compute_has_multiple_packages(self):
        for shipment in self:
            shipment.has_multiple_packages = shipment.nbr_colis > 1

    @api.depends('reference_from', 'nbr_colis')
    def _compute_reference_to(self):
        """Auto-calculate reference_to from reference_from + nbr_colis"""
        for shipment in self:
            if shipment.reference_from and shipment.nbr_colis > 0:
                try:
                    ref_start = int(shipment.reference_from)
                    ref_end = ref_start + shipment.nbr_colis
                    shipment.reference_to = str(ref_end)
                except (ValueError, TypeError):
                    # If reference_from is not a number, keep it as is
                    shipment.reference_to = shipment.reference_from
            else:
                shipment.reference_to = shipment.reference_from or False

    @api.depends('reference', 'reference_from', 'reference_to', 'nbr_colis')
    def _compute_reference_display(self):
        for shipment in self:
            if shipment.nbr_colis > 1:
                if shipment.reference_from and shipment.reference_to:
                    shipment.reference_display = f"{shipment.reference_from} → {shipment.reference_to}"
                elif shipment.reference_from:
                    shipment.reference_display = shipment.reference_from
                else:
                    shipment.reference_display = False
            else:
                shipment.reference_display = shipment.reference or False

    def get_reference_list(self):
        """Generate list of reference numbers for label printing."""
        self.ensure_one()
        refs = []
        try:
            ref_from = int(self.reference_from or 0)
            ref_to = int(self.reference_to or ref_from)
            for num in range(ref_from, ref_to + 1):
                refs.append(str(num))
        except (ValueError, TypeError):
            # If conversion fails, return reference_from or name
            if self.reference_from:
                refs.append(self.reference_from)
            elif self.reference:
                refs.append(self.reference)
            else:
                refs.append(self.name)
        return refs

    @api.depends('package_ids', 'package_ids.gab')
    def _compute_package_summary(self):
        for shipment in self:
            packages = shipment.package_ids
            shipment.package_count = len(packages)
            if packages:
                first_gab = packages[0].gab
                last_gab = packages[-1].gab
                if len(packages) == 1:
                    shipment.gab_range = first_gab
                else:
                    shipment.gab_range = f"{first_gab} → {last_gab}"
            else:
                shipment.gab_range = False

    @api.depends('gab')
    def _compute_cab1(self):
        for shipment in self:
            if shipment.gab:
                shipment.cab1 = f'*{shipment.gab}*'
            else:
                shipment.cab1 = False

    @api.depends('partner_id', 'partner_id.mobile', 'partner_id.phone')
    def _compute_ms_destinataire(self):
        for shipment in self:
            partner = shipment.partner_id
            if partner:
                # Prefer mobile, fallback to phone
                shipment.ms_destinataire = partner.mobile or partner.phone or ''
            else:
                shipment.ms_destinataire = ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('delivery.shipment') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the shipment."""
        for shipment in self:
            if shipment.is_barid and not shipment.package_ids:
                raise UserError(_("Please generate barcodes before confirming."))
            shipment.state = 'confirmed'

    def action_in_transit(self):
        """Mark shipment as in transit."""
        self.write({'state': 'in_transit'})

    def action_deliver(self):
        """Mark shipment as delivered."""
        self.write({
            'state': 'delivered',
            'delivery_date': fields.Date.today(),
        })

    def action_return(self):
        """Mark shipment as returned."""
        self.write({'state': 'returned'})

    def action_cancel(self):
        """Cancel the shipment."""
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Reset to draft."""
        self.write({'state': 'draft'})

    def action_generate_barcode(self):
        """Generate packages based on number of colis.
        - Barid: Creates packages with GAB barcodes
        - Non-Barid: Creates packages with reference numbers
        """
        for shipment in self:
            if shipment.package_ids:
                raise UserError(_("Packages already exist. Clear them first to generate new ones."))
            
            nbr = shipment.nbr_colis or 1
            packages = []
            
            if shipment.is_barid:
                # Barid: Generate GAB barcodes
                for i in range(nbr):
                    sequence = self.env['ir.sequence'].next_by_code('delivery.shipment.barcode') or '000000001'
                    gab = f'LI{sequence}MA'
                    packages.append((0, 0, {
                        'gab': gab,
                        'sequence': i + 1,
                    }))
                
                shipment.write({'package_ids': packages})
                
                # Set main GAB to first package GAB for backward compatibility
                if shipment.package_ids:
                    shipment.gab = shipment.package_ids[0].gab
            else:
                # Non-Barid: Use reference range
                try:
                    ref_start = int(shipment.reference_from or 0)
                except (ValueError, TypeError):
                    ref_start = 0
                
                for i in range(nbr):
                    ref_num = str(ref_start + i) if ref_start else f"REF-{i + 1}"
                    packages.append((0, 0, {
                        'reference': ref_num,
                        'sequence': i + 1,
                    }))
                
                shipment.write({'package_ids': packages})

    def action_clear_barcodes(self):
        """Clear all package barcodes."""
        for shipment in self:
            shipment.package_ids.unlink()
            shipment.gab = False

    def action_view_packages(self):
        """Open popup to view all packages."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Packages - %s') % self.name,
            'res_model': 'delivery.shipment.package',
            'view_mode': 'list',
            'domain': [('shipment_id', '=', self.id)],
            'context': {'default_shipment_id': self.id},
            'target': 'new',
        }

    def action_open_picking(self):
        """Open related delivery order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Order'),
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
