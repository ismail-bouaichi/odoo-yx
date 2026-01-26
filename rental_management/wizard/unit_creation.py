# -*- coding: utf-8 -*-
# Copyright 2023-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


# Unit Create from Project
class UnitCreation(models.TransientModel):
    """Unit Creation"""
    _name = 'unit.creation'
    _description = 'Project Unit Creation'

    total_floors = fields.Integer(string="Total Floors", default="1")
    units_per_floor = fields.Integer(string="Units per Floor", default="1")
    property_code_prefix = fields.Char(string="Prefix",
                                       help="Prefix for Property Code")
    floor_start_from = fields.Integer(string="Floor Start From")
    
    # New fields for setting price and area on created units
    unit_price = fields.Float(string="Unit Price", 
                              help="Sale price for each created unit")
    unit_area = fields.Float(string="Unit Area (m²)", 
                             help="Total area in square meters for each unit")
    
    # Special floor fields - for floors with different unit counts
    has_special_floor = fields.Boolean(string="Exceptions par étage?",
                                        help="Check if one floor has a different number of units")
    special_floor_number = fields.Integer(string="Numéro de l'étage spécial",
                                           help="The floor number that has a different unit count")
    special_floor_units = fields.Integer(string="Nombre d'unités sur cet étage",
                                          help="Number of units on the special floor")

    @api.model
    def default_get(self, fields_list):
        """Default get"""
        res = super(UnitCreation, self).default_get(fields_list)
        active_id = self._context.get("active_id", False)
        unit_from = self._context.get('unit_from')
        if unit_from == 'project':
            project_id = self.env["property.project"].browse(active_id)
            res['property_code_prefix'] = project_id.project_sequence
            res['floor_start_from'] = project_id.floor_created + 1
        elif unit_from == 'sub_project':
            project_id = self.env["property.sub.project"].browse(active_id)
            res['property_code_prefix'] = project_id.project_sequence
            res['total_floors'] = project_id.total_floors
            res['units_per_floor'] = project_id.units_per_floor
            res['floor_start_from'] = project_id.floor_created + 1
        return res

    def action_create_property_unit(self):
        """Create property unit from project or subproject"""
        created_ids = []
        active_id = self._context.get("active_id", False)
        unit_from = self._context.get('unit_from')
        property_rec = {}
        project_id = False
        if self.total_floors <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Total Floor !'),
                    'message': _("Total floor should be greater than 1."),
                    'sticky': False,
                }
            }
        if self.units_per_floor <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Total Unit Per Floor !'),
                    'message': _('Total unit per floor should be greater than 1.'),
                    'sticky': False,
                }
            }
        if not active_id:
            return
        if unit_from == 'project':
            project_id = self.env["property.project"].browse(active_id)
            property_rec['property_project_id'] = project_id.id
        elif unit_from == 'sub_project':
            project_id = self.env["property.sub.project"].browse(active_id)
            property_rec['property_project_id'] = project_id.property_project_id.id
            property_rec['subproject_id'] = project_id.id
        if not project_id:
            return
        if project_id.project_for == 'rent':
            property_rec['sale_lease'] = 'for_tenancy'
        if project_id.project_for == 'sale':
            property_rec['sale_lease'] = 'for_sale'
        property_static_rec = {
            'total_floor': self.total_floors,
            'property_subtype_id': project_id.property_subtype_id.id,
            'landlord_id': project_id.landlord_id.id,
            'type': project_id.property_type,
            'street': project_id.street,
            'street2': project_id.street2,
            'city_id': project_id.city_id.id,
            'zip': project_id.zip,
            'state_id': project_id.state_id.id,
            'country_id': project_id.country_id.id,
            'region_id': project_id.region_id.id,
            'website': project_id.website,
            'longitude': project_id.longitude,
            'latitude': project_id.latitude,
            # New fields: price and area from wizard
            'price': self.unit_price,
            'total_area': self.unit_area,
        }
        property_rec.update(property_static_rec)
        property_data = []
        for floor in range(self.floor_start_from, self.total_floors + self.floor_start_from):
            # Determine number of units for this floor
            if self.has_special_floor and floor == self.special_floor_number:
                floor_units = self.special_floor_units
            else:
                floor_units = self.units_per_floor
            
            for unit in range(1, floor_units + 1):
                code = "%s%s-%s" % (self.property_code_prefix,
                                    str(floor).zfill(2), str(unit).zfill(2))
                name = "%s-%s" % (project_id.name,
                                  str(floor) + str(unit).zfill(2))
                floor_now = floor
                property_data.append({
                    "name": name,
                    "property_seq": code,
                    "floor": floor_now
                })
        unit_amenities, unit_images, unit_specification, unit_connectivity = self.get_property_availability(
            unit_from=unit_from,
            project_id=project_id
        )
        availability_info = self.get_property_availability_info(
            project_id=project_id,
            unit_amenities=unit_amenities,
            unit_specification=unit_specification,
            unit_images=unit_images,
            unit_connectivity=unit_connectivity
        )
        property_rec.update(availability_info)
        # Property Data
        for data in property_data:
            property_rec['name'] = data.get('name')
            property_rec['property_seq'] = data.get('property_seq')
            property_rec['floor'] = data.get('floor')
            property_id = self.env['property.details'].sudo().create(
                property_rec)
            created_ids.append(property_id.id)
        project_id.write({
            'total_floors': self.total_floors,
            'units_per_floor': self.units_per_floor,
            'floor_created': project_id.floor_created + self.total_floors
        })
        return {
            "name": "Properties",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", created_ids)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }

    def get_property_availability(self, unit_from, project_id):
        """Process property availability"""
        unit_amenities = False
        unit_images = False
        unit_specification = False
        unit_connectivity = False
        if unit_from == 'project':
            unit_amenities = project_id.property_amenity_ids.ids
            unit_images = project_id.project_image_ids
            unit_specification = project_id.property_specification_ids.ids
            unit_connectivity = project_id.project_connectivity_ids
        if unit_from == 'sub_project':
            unit_amenities = project_id.subproject_amenity_ids.ids
            unit_images = project_id.subproject_image_ids
            unit_specification = project_id.subproject_specification_ids.ids
            unit_connectivity = project_id.subproject_connectivity_ids
        return unit_amenities, unit_images, unit_specification, unit_connectivity

    def get_property_availability_info(self, project_id, unit_amenities, unit_specification,
                                       unit_images, unit_connectivity):
        """Get property availability from project"""
        info_rec = {}
        images = []
        nearby = []
        # Amenities
        if project_id.avail_amenity:
            info_rec['amenities'] = project_id.avail_amenity
            info_rec['amenities_ids'] = unit_amenities
        # Specifications
        if project_id.avail_specification:
            info_rec['is_facilities'] = project_id.avail_specification
            info_rec['property_specification_ids'] = unit_specification
        # Images
        if project_id.avail_image:
            info_rec['is_images'] = project_id.avail_image
            for image in unit_images:
                images.append((0, 0, {
                    'title': image.title,
                    'sequence': image.sequence,
                    'image': image.image,
                    'video_url': image.video_url,
                }))
            info_rec['property_images_ids'] = images
        # Connectivity
        if project_id.avail_nearby_connectivity:
            info_rec['nearby_connectivity'] = project_id.avail_nearby_connectivity
            for n in unit_connectivity:
                nearby.append((0, 0, {
                    'connectivity_id': n.connectivity_id.id,
                    'name': n.name,
                    'image': n.image,
                    'distance': n.distance
                }))
            info_rec['connectivity_ids'] = nearby
        return info_rec
