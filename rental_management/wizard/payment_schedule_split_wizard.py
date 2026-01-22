# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentScheduleSplitWizard(models.TransientModel):
    _name = 'payment.schedule.split.wizard'
    _description = 'Split a Payment Schedule Line'

    line_id = fields.Many2one('property.payment.schedule', required=True, string="Installment")
    # Split en 2
    amount1 = fields.Monetary(string="Amount 1", required=True)
    date1 = fields.Date(string="Due Date 1", required=True)
    label1 = fields.Char(string="Label 1")

    amount2 = fields.Monetary(string="Amount 2", required=True)
    date2 = fields.Date(string="Due Date 2", required=True)
    label2 = fields.Char(string="Label 2")

    company_id = fields.Many2one(related='line_id.company_id', store=False)
    currency_id = fields.Many2one(related='line_id.currency_id', store=False)

    def action_split(self):
        self.ensure_one()
        if not self.line_id:
            raise UserError(_("No line to split."))
        return self.line_id.action_split(
            amount1=self.amount1, date1=self.date1,
            amount2=self.amount2, date2=self.date2,
            label1=self.label1, label2=self.label2
        )
