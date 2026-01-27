# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

FREQ_SELECTION = [
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
]


class PaymentScheduleGenerateWizard(models.TransientModel):
    _name = 'payment.schedule.generate.wizard'
    _description = 'Generate Payment Schedule linked to Sale/Booking'

    vendor_id = fields.Many2one('property.vendor', string="Sale/Booking", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    property_id = fields.Many2one('property.details', string="Property")
    final_price = fields.Monetary(string='Final Price')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)

    # MODE
    generate_mode = fields.Selection([
        ('by_calendar', 'By Calendar (dates)'),
        ('by_number', 'By Number (no dates)'),
    ], default='by_calendar', required=True)

    first_due_date = fields.Date(string="First Due Date", default=fields.Date.today)
    frequency = fields.Selection(FREQ_SELECTION, default='monthly')

    installments = fields.Integer(string="Installments", default=1)
    down_payment = fields.Monetary(string="Down Payment", default=0.0)

    @api.onchange('vendor_id')
    def _onchange_vendor_defaults(self):
        if self.vendor_id:
            # essaie de préremplir depuis la vente
            self.partner_id = getattr(self.vendor_id, 'customer_id', False) or self.partner_id
            self.property_id = getattr(self.vendor_id, 'property_id', False) or self.property_id

    def action_generate(self):
        self.ensure_one()
        if self.installments <= 0:
            raise UserError(_("Installments must be a positive integer."))

        if not self.partner_id or not self.property_id:
            raise UserError(_("Partner and Property are required."))

        Schedule = self.env['property.payment.schedule']

        base_amount = (self.final_price or 0.0) - (self.down_payment or 0.0)
        self.vendor_id.sale_price = self.final_price
        if base_amount < 0:
            raise UserError(_("Down Payment cannot exceed the total amount."))

        # Acompte (optionnel)
        if self.down_payment:
            Schedule.create({
                'name': _("Reservation (Paid)"),
                'partner_id': self.partner_id.id,
                'property_id': self.property_id.id,
                'vendor_id': self.vendor_id.id,
                'company_id': self.company_id.id,
                'amount': abs(self.down_payment),  # Force positive to prevent validation errors
                'due_date': self.first_due_date if self.generate_mode == 'by_calendar' else False,
                'state': 'pending',                   # Mark as paid immediately
                'validation_state': 'to_provide',   # Auto-validate
            })

        # Répartition équitable
        amount_each = round(base_amount / self.installments, 2)
        tail = round(base_amount - amount_each * (self.installments - 1), 2)

        def _next_date(prev):
            if not prev:
                return False
            if self.frequency == 'weekly':
                return fields.Date.to_date(prev) + relativedelta(weeks=1)
            if self.frequency == 'monthly':
                return fields.Date.to_date(prev) + relativedelta(months=1)
            if self.frequency == 'quarterly':
                return fields.Date.to_date(prev) + relativedelta(months=3)
            return prev

        current_date = self.first_due_date if self.generate_mode == 'by_calendar' else False
        for i in range(1, self.installments + 1):
            amt = tail if i == self.installments else amount_each
            Schedule.create({
                'name': _("Installment %s/%s") % (i, self.installments),
                'partner_id': self.partner_id.id,
                'property_id': self.property_id.id,
                'vendor_id': self.vendor_id.id,
                'company_id': self.company_id.id,
                'amount': amt,
                'due_date': current_date if self.generate_mode == 'by_calendar' else False,
                'state': 'pending',
                'validation_state': 'to_provide',
            })
            if self.generate_mode == 'by_calendar':
                current_date = _next_date(current_date)
