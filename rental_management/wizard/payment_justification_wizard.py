# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentJustificationWizard(models.TransientModel):
    _name = 'payment.justification.wizard'
    _description = 'Attach a Payment Document for Validation'

    line_id = fields.Many2one('property.payment.schedule', required=True, string="Installment")
    document = fields.Binary(string="Payment Document", required=True, attachment=True)
    filename = fields.Char(string="Filename")
    description = fields.Char(string="Description")

    def action_submit(self):
        self.ensure_one()
        line = self.line_id
        if line.validation_state == 'validated':
            raise UserError(_("This installment is already validated."))

        attach = self.env['ir.attachment'].create({
            'name': self.filename or _("Payment Document"),
            'datas': self.document,
            'res_model': line._name,
            'res_id': line.id,
            'mimetype': False,
            'description': self.description or False,
        })
        line.payment_doc_id = attach.id
        line.validation_state = 'doc_submitted'
        return {'type': 'ir.actions.act_window_close'}
