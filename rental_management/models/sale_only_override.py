# -*- coding: utf-8 -*-
# Override fields to remove Rent option - Sales Only Mode

from odoo import api, fields, models, _


class PropertyProjectSaleOnly(models.Model):
    """Override property.project to remove Rent option"""
    _inherit = "property.project"

    # Override project_for to only have Sale option
    project_for = fields.Selection(
        selection=[("sale", "Vente")],
        string="Projet Pour",
        default='sale',
        required=True
    )

    # Override sale_lease (Valuation of) to only have Sale option
    sale_lease = fields.Selection(
        selection=[("sale", "Vente")],
        string='Évaluation de',
        default='sale',
        required=True
    )

    # Add new property type: Residential and Commercial
    property_type = fields.Selection(
        selection=[
            ("residential", "Résidentiel"),
            ("commercial", "Commercial"),
            ("industrial", "Industriel"),
            ("land", "Terrain"),
            ("residential_commercial", "Résidentiel et Commercial"),
        ],
        string="Type de Bien",
        required=True
    )


class PropertySubProjectSaleOnly(models.Model):
    """Override property.sub.project to remove Rent option"""
    _inherit = "property.sub.project"

    # Override project_for to only have Sale option
    project_for = fields.Selection(
        selection=[("sale", "Vente")],
        string="Bloc Pour",
        default='sale',
        required=True
    )

    # Override sale_lease to only have Sale option
    sale_lease = fields.Selection(
        selection=[("sale", "Vente")],
        string="Évaluation de",
        default='sale',
        required=True
    )


class PropertyDetailsSaleOnly(models.Model):
    """Override property.details to remove Rent option"""
    _inherit = "property.details"

    # Override sale_lease to only have Sale option
    sale_lease = fields.Selection(
        selection=[("sale", "Vente")],
        string='Bien Pour',
        default='sale',
        required=True
    )

    # Add new property type: Residential and Commercial
    type = fields.Selection(
        selection=[
            ('land', 'Terrain'),
            ('residential', 'Résidentiel'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industriel'),
            ('residential_commercial', 'Résidentiel et Commercial'),
        ],
        string='Type de Bien',
        required=True,
        default='residential'
    )


class PropertySubTypeSaleOnly(models.Model):
    """Override property.sub.type to add new property type option"""
    _inherit = "property.sub.type"

    # Add new property type: Residential and Commercial
    type = fields.Selection(
        selection=[
            ('land', 'Terrain'),
            ('residential', 'Résidentiel'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industriel'),
            ('residential_commercial', 'Résidentiel et Commercial'),
        ],
        string='Type'
    )
