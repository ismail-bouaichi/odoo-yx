from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_company_id = fields.Many2one(
        'delivery.company', 
        string='Delivery Company',
        help="Delivery company used for shipping to this customer",
        default=lambda self: self.env['delivery.company'].search(
            [('provider_type', '=', 'barid'), ('active', '=', True)],
            limit=1
        )
    )
    
    def write(self, vals):
        """Auto-assign default delivery company when customer_rank increases."""
        res = super().write(vals)
         
        if vals.get('customer_rank', 0) > 0:
            default_company = self.env['delivery.company'].search(
                [('provider_type', '=', 'barid'), ('active', '=', True)],
                limit=1
            )
            if default_company:
                for partner in self:
                    if partner.customer_rank > 0 and not partner.delivery_company_id:
                        partner.delivery_company_id = default_company
        return res
