# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class RealEstateInstallment(models.Model):
    _name = "real.estate.installment"
    _description = "Échéance Immobilier (hors compta)"
    _order = "due_date asc, id asc"

    name = fields.Char(required=True, default=lambda s: _("Échéance"))
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict")
    property_id = fields.Many2one("property.details", string="Bien", ondelete="restrict", required=True)

    currency_id = fields.Many2one(
        "res.currency", required=True, default=lambda s: s.env.company.currency_id.id
    )
    # Montant attendu pour CETTE échéance (pas la valeur totale du bien)
    amount = fields.Monetary(string="Montant échéance", required=True)
    due_date = fields.Date(string="Date d’échéance", required=True)
    note = fields.Text()

    # Paiements internes (pas d’écriture comptable)
    payment_ids = fields.One2many("real.estate.installment.payment", "installment_id", string="Règlements")
    paid_amount = fields.Monetary(string="Total payé", compute="_compute_paid", currency_field="currency_id", store=True)
    residual_amount = fields.Monetary(string="Reste à payer", compute="_compute_paid", currency_field="currency_id", store=True)

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("partial", "Partiellement payé"),
            ("paid", "Payée"),
            ("late", "En retard"),
        ],
        compute="_compute_state",
        store=True,
        default="draft",
    )

    @api.depends("payment_ids.amount", "amount")
    def _compute_paid(self):
        for rec in self:
            total_paid = sum(rec.payment_ids.mapped("amount"))
            rec.paid_amount = total_paid
            rec.residual_amount = max(rec.amount - total_paid, 0.0)

    @api.depends("due_date", "residual_amount", "paid_amount", "amount")
    def _compute_state(self):
        today = date.today()
        for rec in self:
            if rec.paid_amount <= 0:
                # rien payé
                rec.state = "draft" if (not rec.due_date or rec.due_date >= today) else "late"
            elif rec.residual_amount <= 0:
                rec.state = "paid"
            else:
                rec.state = "partial"
                if rec.due_date and rec.due_date < today:
                    rec.state = "late"

    @api.constrains("amount")
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Le montant de l'échéance doit être > 0."))

    def action_open_register_payment(self):
        """Ouvre le wizard interne d’enregistrement d’un règlement (hors compta)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Enregistrer un règlement"),
            "res_model": "real.estate.installment.register.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_installment_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_currency_id": self.currency_id.id,
                "residual_amount": self.residual_amount,
            },
        }


class RealEstateInstallmentPayment(models.Model):
    _name = "real.estate.installment.payment"
    _description = "Règlement d'échéance (hors compta)"
    _order = "payment_date asc, id asc"

    installment_id = fields.Many2one("real.estate.installment", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict")
    currency_id = fields.Many2one("res.currency", required=True, default=lambda s: s.env.company.currency_id.id)

    payment_date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    amount = fields.Monetary(string="Montant", required=True)
    reference = fields.Char(string="Référence")
    note = fields.Text()

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Le montant du règlement doit être > 0."))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        # Recalculer la résiduelle de l'échéance
        recs.mapped("installment_id")._compute_paid()
        recs.mapped("installment_id")._compute_state()
        return recs

    def write(self, vals):
        res = super().write(vals)
        self.mapped("installment_id")._compute_paid()
        self.mapped("installment_id")._compute_state()
        return res

    def unlink(self):
        installments = self.mapped("installment_id")
        res = super().unlink()
        installments._compute_paid()
        installments._compute_state()
        return res