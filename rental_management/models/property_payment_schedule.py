# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyPaymentSchedule(models.Model):
    _name = 'property.payment.schedule'
    _description = 'Property Payment Schedule (No Invoices)'
    _order = "due_date asc, id asc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Label", tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, index=True)
    property_id = fields.Many2one('property.details', string="Property", index=True)
    vendor_id = fields.Many2one('property.vendor', string="Sale/Booking", required=True, ondelete="cascade", index=True)

    company_id = fields.Many2one('res.company', default=lambda s: s.env.company, string="Company", required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)

    # Montants
    amount = fields.Monetary(string="Amount", required=True, tracking=True)
    residual_amount = fields.Monetary(string="Residual", compute='_compute_residual', store=True)
    paid_amount = fields.Monetary(string="Paid", compute='_compute_paid', store=True)


    # Échéance (peut être vide si mode “par nombre”)
    due_date = fields.Date(string="Due Date", tracking=True)

    # États de paiement de la ligne
    state = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], default='pending', string="Pay Status", tracking=True)

    # Validation documentaire (justificatif obligatoire)
    validation_state = fields.Selection([
        ('to_provide', 'Doc to Provide'),
        ('doc_submitted', 'Doc Submitted'),
        ('validated', 'Validated'),
    ], default='to_provide', string="Validation", tracking=True)

    payment_doc_id = fields.Many2one('ir.attachment', string="Payment Document", copy=False, index=True)

    # Paiement comptable simple (sans facture)
    payment_id = fields.Many2one('account.payment', string="Payment", copy=False)
    payment_state = fields.Selection(related='payment_id.state', string="Payment State", store=True)

    note = fields.Text(string="Note")

    # --- COMPUTES ---

    @api.depends('payment_id.state', 'payment_id.amount', 'amount')
    def _compute_paid(self):
        for rec in self:
            if rec.payment_id and rec.payment_id.state == 'paid':
                rec.paid_amount = min(rec.payment_id.amount, rec.amount)
            else:
                rec.paid_amount = 0.0

    @api.depends('amount', 'paid_amount', 'state')
    def _compute_residual(self):
        for rec in self:
            rec.residual_amount = max(rec.amount - rec.paid_amount, 0.0)

    @api.onchange('payment_state', 'paid_amount', 'amount')
    def _onchange_status_by_payment(self):
        for rec in self:
            if rec.state == 'cancel':
                continue
            if rec.paid_amount <= 0:
                rec.state = 'pending'
            elif 0 < rec.paid_amount < rec.amount:
                rec.state = 'partial'
            else:
                rec.state = 'paid'

    # --- ACTIONS ---

    def action_register_payment(self):
        """Créer / ouvrir un account.payment (sans facture)."""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("This installment is already paid."))

        if self.payment_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Payment'),
                'res_model': 'account.payment',
                'view_mode': 'form',
                'res_id': self.payment_id.id,
                'target': 'current',
            }

        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.residual_amount or self.amount,
            'currency_id': self.currency_id.id,
            'name': self.name or _("Installment"),
            'date': fields.Date.context_today(self),
            'journal_id': self.env['account.journal'].search([
                ('type', '=', 'bank'),
                ('company_id', '=', self.company_id.id)
            ], limit=1).id or False,
        }
        payment = self.env['account.payment'].create(payment_vals)
        self.payment_id = payment.id
        self.state = 'paid'

        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }

    def action_submit_payment_doc(self):
        """Ouvre le wizard pour attacher une justification (obligatoire pour valider)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Submit Payment Document'),
            'res_model': 'payment.justification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_line_id': self.id},
        }

    def action_validate_with_doc(self):
        """
        Valide l'échéance SI et seulement si :
        - un document de paiement est attaché,
        - et si un payment existe, il doit être 'posted'.
        """
        for rec in self:
            if not rec.payment_doc_id:
                raise UserError(_("A payment document is required to validate this installment."))
            if rec.payment_id and rec.payment_id.state != 'paid':
                raise UserError(_("The linked payment must be 'Posted' to validate this installment."))
            rec.validation_state = 'validated'

    def action_split(self, amount1, date1, amount2, date2, label1=None, label2=None):
        """Split manuel: remplace la ligne par 2 lignes (même vendor)."""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("Cannot split a paid installment."))

        if (amount1 or 0) <= 0 or (amount2 or 0) <= 0:
            raise UserError(_("Split amounts must be strictly positive."))

        # si partiellement payée, on autorise split uniquement sur le résiduel
        base = self.residual_amount if self.paid_amount else self.amount
        if round(amount1 + amount2, 2) != round(base, 2):
            raise UserError(_("Split total must equal the line amount (or residual if partially paid)."))

        if self.payment_id and self.payment_id.state != 'draft':
            raise UserError(_("This line has a linked payment not in draft; cancel or reset it first."))

        vals_common = {
            'partner_id': self.partner_id.id,
            'property_id': self.property_id.id,
            'vendor_id': self.vendor_id.id,
            'company_id': self.company_id.id,
        }
        self.write({'state': 'cancel'})  # on neutralise la ligne originale

        self.create({
            **vals_common,
            'name': label1 or (self.name and f"{self.name} (1/2)") or _("Installment (1/2)"),
            'amount': amount1,
            'due_date': date1,
            'state': 'pending',
            'validation_state': 'to_provide',
        })
        self.create({
            **vals_common,
            'name': label2 or (self.name and f"{self.name} (2/2)") or _("Installment (2/2)"),
            'amount': amount2,
            'due_date': date2,
            'state': 'pending',
            'validation_state': 'to_provide',
        })
        return True


# ---- Agrégats & smart buttons côté VENTE ----

class PropertyVendor(models.Model):
    _inherit = 'property.vendor'

    schedule_count = fields.Integer(compute='_compute_schedule_count', string="Installments")
    amount_scheduled = fields.Monetary(string="Scheduled", compute='_compute_amounts', currency_field='company_currency_id')
    amount_paid = fields.Monetary(string="Paid", compute='_compute_amounts', currency_field='company_currency_id')
    amount_residual = fields.Monetary(string="Residual", compute='_compute_amounts', currency_field='company_currency_id')
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    def _compute_schedule_count(self):
        Schedule = self.env['property.payment.schedule']
        for rec in self:
            rec.schedule_count = Schedule.search_count([('vendor_id', '=', rec.id)])

    def _compute_amounts(self):
        Schedule = self.env['property.payment.schedule']
        for rec in self:
            lines = Schedule.search([('vendor_id', '=', rec.id)])
            rec.amount_scheduled = sum(lines.mapped('amount'))
            rec.amount_paid = sum(lines.mapped('paid_amount'))
            rec.amount_residual = sum(lines.mapped('residual_amount'))

    def action_view_schedule(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Schedule'),
            'res_model': 'property.payment.schedule',
            'view_mode': 'list,form',
            'domain': [('vendor_id', '=', self.id)],
            'context': {
                'default_partner_id': self.customer_id.id if hasattr(self, 'customer_id') and self.customer_id else False,
                'default_property_id': self.property_id.id if hasattr(self, 'property_id') and self.property_id else False,
                'default_vendor_id': self.id,
            },
        }
