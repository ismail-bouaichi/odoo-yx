# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertyPreSaleWizard(models.TransientModel):
    _name = 'property.presale.wizard'
    _description = 'Create a Pre-sale (Option) for a Property'

    property_id = fields.Many2one('property.details', string='Property', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('user_type','=','customer')]"
    )
    validity_days = fields.Integer(string='Validity (days)', default=7, required=True)
    amount = fields.Monetary(string='Deposit Amount')
    note = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)

    def action_create_presale(self):
        self.ensure_one()
        presale = self.env['property.presale'].create({
            'property_id': self.property_id.id,
            'partner_id': self.partner_id.id,
            'validity_days': self.validity_days,
            'amount': self.amount,
            'note': self.note,
            'state': 'active',
        })
        presale.action_activate()
        return {'type': 'ir.actions.act_window_close'}
