# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_company_id = fields.Many2one(
        'delivery.company',
        string='Delivery Company',
        help="Delivery company for this shipment",
    )

    def _get_sale_order(self):
        """Get the sale order linked to this picking."""
        self.ensure_one()
        
        if self.sale_id:
            return self.sale_id
        
        if self.group_id and self.group_id.sale_id:
            return self.group_id.sale_id
        
        if self.origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
            if sale_order:
                return sale_order
        return False

    def write(self, vals):
        """When delivery company changes on OUT, update related documents of the day."""
        res = super().write(vals)
        
        if self.env.context.get('skip_propagation'):
            return res
        
        if 'delivery_company_id' in vals:
            for picking in self:
                if picking.picking_type_code == 'outgoing':
                    picking._propagate_delivery_company_changes()
        return res

    def _propagate_delivery_company_changes(self):
        """Propagate delivery company changes to related documents created today."""
        self.ensure_one()
        today = date.today()
        
        sale_order = self._get_sale_order()
        if sale_order and sale_order.date_order.date() == today:
            sale_order.write({
                'delivery_company_id': self.delivery_company_id.id,
            })
        
        if self.group_id:
            related_pickings = self.env['stock.picking'].search([
                ('group_id', '=', self.group_id.id),
                ('id', '!=', self.id),
                ('create_date', '>=', fields.Datetime.to_string(today)),
            ])
            for pick in related_pickings:
                pick.with_context(skip_propagation=True).write({
                    'delivery_company_id': self.delivery_company_id.id,
                })
    
        if sale_order:
            invoices = sale_order.invoice_ids.filtered(
                lambda inv: inv.state == 'draft'
            )
            invoices.write({
                'delivery_company_id': self.delivery_company_id.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        """Fill delivery company from sale order on creation."""
        pickings = super().create(vals_list)
        for picking in pickings:
            sale_order = picking._get_sale_order()
            if sale_order and not picking.delivery_company_id and sale_order.delivery_company_id:
                picking.with_context(skip_propagation=True).write({
                    'delivery_company_id': sale_order.delivery_company_id.id,
                })
        return pickings

    def _action_done(self):
        """Propagate delivery company to next pickings in the chain when validated."""
        res = super()._action_done()
        for picking in self:
            next_pickings = picking.move_ids.move_dest_ids.picking_id.filtered(lambda p: p)
            for next_picking in next_pickings:
                if not next_picking.delivery_company_id and picking.delivery_company_id:
                    next_picking.with_context(skip_propagation=True).write({
                        'delivery_company_id': picking.delivery_company_id.id,
                    })
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """Pass delivery company to pickings when confirming sale order."""
        res = super()._action_confirm()
        for order in self:
            for picking in order.picking_ids:
                if not picking.delivery_company_id and order.delivery_company_id:
                    picking.with_context(skip_propagation=True).write({
                        'delivery_company_id': order.delivery_company_id.id,
                    })
        return res
