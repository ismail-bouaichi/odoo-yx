# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class PropertyPreSale(models.Model):
    _name = "property.presale"
    _description = "Pre-sale (Option) for a Property Unit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(string="Reference", default="New", copy=False, readonly=True)
    property_id = fields.Many2one('property.details', string='Property', required=True, ondelete='cascade')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('user_type','=','customer')]"
    )
    date_start = fields.Date(string='Start', default=fields.Date.today, tracking=True)
    validity_days = fields.Integer(string='Validity (days)', default=7, tracking=True)
    date_expiry = fields.Date(string='Expires On', compute='_compute_expiry', store=True)
    amount = fields.Monetary(string='Deposit Amount')
    note = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('converted', 'Converted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Company')
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    is_expired = fields.Boolean(compute='_compute_is_expired', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('property.presale') or 'New'
        return super().create(vals_list)

    @api.depends('date_start', 'validity_days')
    def _compute_expiry(self):
        for rec in self:
            if rec.date_start and rec.validity_days is not None:
                rec.date_expiry = rec.date_start + timedelta(days=rec.validity_days)
            else:
                rec.date_expiry = False

    @api.depends('date_expiry', 'state')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = bool(rec.date_expiry and rec.date_expiry < today and rec.state in ('draft', 'active'))

    def action_activate(self):
        for rec in self:
            if rec.property_id.stage not in ('available', 'sale', 'pre_sale'):
                raise UserError(_('The property must be available or in sale to set a pre-sale.'))
            rec.state = 'active'
            rec.property_id.write({'stage': 'pre_sale', 'presale_id': rec.id, 'customer_id': rec.partner_id.id})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancelled'})
            if rec.property_id.presale_id == rec:
                rec.property_id.write({'presale_id': False, 'stage': 'available'})

    def action_mark_expired(self):
        for rec in self:
            if rec.state in ('converted', 'cancelled'):
                continue
            rec.write({'state': 'expired'})
            if rec.property_id.presale_id == rec:
                rec.property_id.write({'presale_id': False, 'stage': 'available'})

    def action_convert_to_booking(self):
        self.ensure_one()
        if self.is_expired or self.state not in ('active',):
            raise UserError(_('Only active pre-sales can be converted.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking'),
            'res_model': 'booking.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.property_id.id,
                'default_customer_id': self.partner_id.id,
                'from_presale': True,
            }
        }


class PropertyDetailsPreSale(models.Model):
    _inherit = 'property.details'

    customer_id = fields.Many2one('res.partner', string="Customer")
    presale_id = fields.Many2one('property.presale', string='Active Pre-sale', copy=False)
    presale_count = fields.Integer(compute='_compute_presale_count')

    @api.depends('presale_id')
    def _compute_presale_count(self):
        Presale = self.env['property.presale']
        for rec in self:
            rec.presale_count = Presale.search_count([('property_id', '=', rec.id)])

    def action_property_presale_wizard(self):
        """Open the Pre-Sale wizard for this property (no external id required)."""
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx.update({'default_property_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Pre-Sale'),
            'res_model': 'property.presale.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_property_book_wizard(self):
        """Open the Pre-Sale wizard for this property (no external id required)."""
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx.update({'default_customer_id': self.customer_id.id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Of Property'),
            'res_model': 'booking.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }