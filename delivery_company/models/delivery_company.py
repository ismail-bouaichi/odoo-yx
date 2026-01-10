# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DeliveryCompany(models.Model):
    _name = 'delivery.company'
    _description = 'Delivery Company'
 
    name = fields.Char(string='Company Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    default_transport_nature = fields.Selection([
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('domicile', 'Home Delivery (À Domicile)'),
    ], string='Default Transport Nature', default='standard',
       help="Default transport nature for this delivery company")
    
    provider_type = fields.Selection([
        ('barid', 'Barid Al-Maghrib (Amana)'),
        ('other', 'Other'),
    ], string='Provider', required=True, default='barid',
       help="Select the delivery service provider")
    
 
    code_contrat = fields.Char(
        string='Code Contrat',
        help="Contract code for Barid Tracking API (codecontrat)")
    secret_key = fields.Char(
        string='Secret Key',
        help="Secret key for Barid Tracking API authentication")
    
    # E-Commerce API credentials
    ecom_password = fields.Char(
        string='E-Commerce Password',
        help="Password for Barid E-Commerce API (used to get token)")
    
    # Token storage (managed by the system)
    ecom_token = fields.Char(
        string='E-Commerce Token',
        readonly=True,
        copy=False,
        help="Current API token (automatically managed)")
    ecom_token_expiry = fields.Datetime(
        string='Token Expiry',
        readonly=True,
        copy=False,
        help="Token expiration time (automatically managed)")
    
     
    api_url = fields.Char(
        string='Shipping API URL',
        help="API URL for shipment creation")
    tracking_url = fields.Char(
        string='Tracking API URL',
        help="API URL for package tracking")
    username = fields.Char(
        string='Username',
        help="API username (for providers using username/password auth)")
    password = fields.Char(
        string='Password',
        help="API password (for providers using username/password auth)")
    api_key = fields.Char(
        string='API Key',
        help="API key (for providers using key-based auth)")
    
    # ==========================================================================
    # Notes & Additional Info
    # ==========================================================================
    notes = fields.Text(string='Notes')
    
 
    def _get_provider(self):
        """
        Get the appropriate provider instance based on provider_type.
        Returns a provider object that implements the BaseDeliveryProvider interface.
        Uses lazy import to avoid circular imports during module loading.
        """
        self.ensure_one()
        
        # Lazy import to avoid circular import issues
        if self.provider_type == 'barid':
            from ..services.barid_provider import BaridProvider
            return BaridProvider(self)
        # Add new providers here:
        # elif self.provider_type == 'ozon':
        #     from ..services.ozon_provider import OzonProvider
        #     return OzonProvider(self)
        else:
            raise UserError(_(
                "Provider '%(provider)s' is not yet implemented.",
                provider=self.provider_type
            ))
    
    # ==========================================================================
    # API Actions
    # ==========================================================================
    def action_test_connection(self):
        """Test the connection to the delivery provider API."""
        self.ensure_one()
        
        provider = self._get_provider()
        result = provider.test_connection()
        
        if result.get('success'):
            # Build success message
            messages = []
            if 'tracking_api' in result:
                messages.append(f"Tracking API: {result['tracking_api'].get('message', 'OK')}")
            if 'ecom_api' in result:
                messages.append(f"E-Commerce API: {result['ecom_api'].get('message', 'OK')}")
            
            message = '\n'.join(messages) if messages else 'Connection successful!'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            # Build error message
            messages = []
            if 'tracking_api' in result and not result['tracking_api'].get('success'):
                messages.append(f"Tracking API: {result['tracking_api'].get('message', 'Failed')}")
            if 'ecom_api' in result and not result['ecom_api'].get('success'):
                messages.append(f"E-Commerce API: {result['ecom_api'].get('message', 'Failed')}")
            
            error_msg = '\n'.join(messages) if messages else 'Connection failed!'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_refresh_token(self):
        """Manually refresh the E-Commerce API token."""
        self.ensure_one()
        
        if self.provider_type != 'barid':
            raise UserError(_("Token refresh is only available for Barid provider."))
        
        provider = self._get_provider()
        result = provider._get_ecom_token(force_refresh=True)
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Token Refreshed'),
                    'message': _('E-Commerce API token has been refreshed successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_(
                "Failed to refresh token: %(error)s",
                error=result.get('error', 'Unknown error')
            ))
    
    def track_package(self, tracking_number):
        """
        Track a package using the configured provider.
        
        Args:
            tracking_number: The tracking number to look up
            
        Returns:
            dict: Tracking result from the provider
        """
        self.ensure_one()
        provider = self._get_provider()
        return provider.track_package(tracking_number)
    
    def create_shipment(self, shipment_data):
        """
        Create a new shipment using the configured provider.
        
        Args:
            shipment_data: dict containing shipment details
            
        Returns:
            dict: Shipment creation result from the provider
        """
        self.ensure_one()
        provider = self._get_provider()
        return provider.create_shipment(shipment_data)
    
    def get_shipping_label(self, tracking_number):
        """
        Get shipping label for a package.
        
        Args:
            tracking_number: The tracking number
            
        Returns:
            dict: Label data from the provider
        """
        self.ensure_one()
        provider = self._get_provider()
        return provider.get_label(tracking_number)
    
    def cancel_shipment(self, tracking_number):
        """
        Cancel a shipment.
        
        Args:
            tracking_number: The tracking number to cancel
            
        Returns:
            dict: Cancellation result from the provider
        """
        self.ensure_one()
        provider = self._get_provider()
        return provider.cancel_shipment(tracking_number)
