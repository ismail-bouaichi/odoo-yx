# -*- coding: utf-8 -*-
"""
Barid Al-Maghrib (Amana) Delivery Provider Implementation
Supports two APIs:
1. Tracking API: For package tracking via ApiTracking.asmx
2. E-Commerce API: For shipment creation via /api/Package/Insert
"""
import logging
import requests
from datetime import datetime, timedelta
from odoo import fields as odoo_fields

from .base_provider import BaseDeliveryProvider

_logger = logging.getLogger(__name__)


class BaridProvider(BaseDeliveryProvider):
    """
    Barid Al-Maghrib provider implementing tracking and shipping APIs.
    
    Tracking API:
        - Endpoint: https://api-bam.barid.ma/publichtrack/ApiTracking.asmx
        - Method: POST with form-data
        - Fields: CodeBordereau, codecontrat, SecretKey
        
    E-Commerce API:
        - Token: GET https://apicom.barid.ma/api/Account/GetToken?password=XXX
        - Shipment: POST https://apicom.barid.ma/api/Package/Insert
        - Auth: Bearer token in header
    """
    
    # API Endpoints
    # Tracking API - using SuiviBordereau method (French for "Track Shipment")
    TRACKING_URL = "https://api-bam.barid.ma/publichtrack/ApiTracking.asmx/SuiviBordereau"
    ECOM_BASE_URL = "https://apicom.barid.ma/api"
    
    # Timeouts (seconds)
    TIMEOUT = 60  # Increased timeout for slow connections
    
    # Token validity duration (in hours) - adjust based on actual API behavior
    TOKEN_VALIDITY_HOURS = 23
    
    @property
    def provider_code(self):
        return 'barid'
    
    @property
    def provider_name(self):
        return 'Barid Al-Maghrib (Amana)'
    
    def _validate_credentials(self):
        """Validate that required credentials are present."""
        errors = []
        
        # Check tracking credentials
        if not self.company.code_contrat:
            errors.append("Code Contrat is required for tracking")
        if not self.company.secret_key:
            errors.append("Secret Key is required for tracking")
            
        # Check e-commerce credentials
        if not self.company.ecom_password:
            errors.append("E-Commerce password is required for shipping")
            
        if errors:
            _logger.warning(f"Barid credential validation warnings: {errors}")
        
        return {'success': len(errors) == 0, 'errors': errors}
    
    def _get_ecom_token(self, force_refresh=False):
        """
        Get a valid E-Commerce API token.
        Uses cached token if still valid, otherwise fetches a new one.
        
        Args:
            force_refresh: If True, always fetch a new token
            
        Returns:
            dict: {'success': bool, 'token': str or None, 'error': str or None}
        """
        # Check if we have a valid cached token
        if not force_refresh and self.company.ecom_token and self.company.ecom_token_expiry:
            # Use Odoo's datetime comparison
            now = odoo_fields.Datetime.now()
            if now < self.company.ecom_token_expiry:
                return {
                    'success': True,
                    'token': self.company.ecom_token
                }
        
        # Fetch new token
        try:
            url = f"{self.ECOM_BASE_URL}/Account/GetToken"
            params = {'password': self.company.ecom_password}
            
            _logger.info(f"Fetching new Barid E-Commerce token from {url}...")
            response = requests.get(url, params=params, timeout=self.TIMEOUT, verify=True)
            
            if response.status_code == 200:
                token = response.text.strip()
                # Remove quotes if present (API sometimes returns "token")
                token = token.strip('"')
                
                if token and token != 'null':
                    # Calculate expiry time using Odoo's datetime
                    expiry = odoo_fields.Datetime.now() + timedelta(hours=self.TOKEN_VALIDITY_HOURS)
                    
                    # Save token to database
                    self.company.sudo().write({
                        'ecom_token': token,
                        'ecom_token_expiry': expiry
                    })
                    
                    _logger.info("Barid E-Commerce token obtained successfully")
                    return {
                        'success': True,
                        'token': token
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Invalid token received from API'
                    }
            else:
                error_msg = f"Token request failed with status {response.status_code}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout while fetching token'
            }
        except requests.RequestException as e:
            _logger.exception("Error fetching Barid token")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self):
        """
        Test connection to Barid APIs.
        Tests both tracking and e-commerce API connectivity.
        """
        results = {
            'success': True,
            'tracking_api': {'success': False, 'message': ''},
            'ecom_api': {'success': False, 'message': ''}
        }
        
        # Test Tracking API with a dummy request
        try:
            _logger.info(f"Testing Tracking API at {self.TRACKING_URL}")
            response = requests.post(
                self.TRACKING_URL,
                data={
                    'CodeBordereau': 'ANP03920060MA',  # Use test tracking number
                    'codecontrat': self.company.code_contrat or '',
                    'SecretKey': self.company.secret_key or ''
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.TIMEOUT,
                verify=True
            )
            _logger.info(f"Tracking API response: {response.status_code} - {response.text[:500] if response.text else 'empty'}")
            # Even if the tracking returns error for invalid code, 
            # a response means the API is reachable
            if response.status_code == 200:
                results['tracking_api'] = {
                    'success': True,
                    'message': f'Tracking API is accessible. Response: {response.text[:100]}'
                }
            else:
                results['tracking_api'] = {
                    'success': False,
                    'message': f'Tracking API returned status {response.status_code}: {response.text[:200] if response.text else "no body"}'
                }
        except requests.RequestException as e:
            results['tracking_api'] = {
                'success': False,
                'message': f'Tracking API error: {str(e)}'
            }
            results['success'] = False
        
        # Test E-Commerce API by fetching token
        token_result = self._get_ecom_token(force_refresh=True)
        if token_result['success']:
            results['ecom_api'] = {
                'success': True,
                'message': 'E-Commerce API token obtained successfully'
            }
        else:
            results['ecom_api'] = {
                'success': False,
                'message': f"E-Commerce API error: {token_result.get('error', 'Unknown error')}"
            }
            results['success'] = False
        
        return results
    
    def track_package(self, tracking_number):
        """
        Track a package using the Barid Tracking API.
        
        Args:
            tracking_number: The CodeBordereau (tracking number)
            
        Returns:
            dict: Tracking information or error
        """
        if not self.company.code_contrat or not self.company.secret_key:
            return {
                'success': False,
                'error': 'Tracking credentials not configured'
            }
        
        try:
            _logger.info(f"Tracking Barid package: {tracking_number}")
            
            response = requests.post(
                self.TRACKING_URL,
                data={
                    'CodeBordereau': tracking_number,
                    'codecontrat': self.company.code_contrat,
                    'SecretKey': self.company.secret_key
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.TIMEOUT,
                verify=True
            )
            
            if response.status_code == 200:
                # Parse the response (adjust based on actual API response format)
                return {
                    'success': True,
                    'tracking_number': tracking_number,
                    'data': response.text
                }
            else:
                return {
                    'success': False,
                    'error': f'Tracking request failed with status {response.status_code}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout while tracking package'
            }
        except requests.RequestException as e:
            _logger.exception(f"Error tracking Barid package {tracking_number}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_shipment(self, shipment_data):
        """
        Create a new shipment using the Barid E-Commerce API.
        
        Args:
            shipment_data: dict containing:
                - recipient_name: Destination name
                - recipient_address: Full address
                - recipient_city: City
                - recipient_phone: Phone number
                - weight: Package weight
                - cod_amount: Cash on delivery amount (optional)
                - description: Package description
                - ... other fields as required by Barid API
                
        Returns:
            dict: Shipment creation result with tracking number
        """
        # Get valid token
        token_result = self._get_ecom_token()
        if not token_result['success']:
            return token_result
        
        token = token_result['token']
        
        try:
            _logger.info("Creating Barid shipment...")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.ECOM_BASE_URL}/Package/Insert"
            
            response = requests.post(
                url,
                json=shipment_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    _logger.info(f"Barid shipment created successfully: {result}")
                    return {
                        'success': True,
                        'data': result
                    }
                except ValueError:
                    return {
                        'success': True,
                        'data': response.text
                    }
            elif response.status_code == 401:
                # Token expired, try once more with fresh token
                _logger.warning("Token expired, refreshing...")
                token_result = self._get_ecom_token(force_refresh=True)
                if token_result['success']:
                    headers['Authorization'] = f"Bearer {token_result['token']}"
                    response = requests.post(
                        url,
                        json=shipment_data,
                        headers=headers,
                        timeout=30
                    )
                    if response.status_code in [200, 201]:
                        return {
                            'success': True,
                            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        }
                return {
                    'success': False,
                    'error': 'Authentication failed even after token refresh'
                }
            else:
                return {
                    'success': False,
                    'error': f'Shipment creation failed with status {response.status_code}: {response.text}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout while creating shipment'
            }
        except requests.RequestException as e:
            _logger.exception("Error creating Barid shipment")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_label(self, tracking_number):
        """
        Get shipping label for a package.
        Note: Barid might not have a separate label API - check documentation.
        
        Args:
            tracking_number: The package tracking number
            
        Returns:
            dict: Label data (PDF binary) or error
        """
        # TODO: Implement when Barid provides label API endpoint
        _logger.warning("Barid label API not yet implemented")
        return {
            'success': False,
            'error': 'Label printing not available for Barid. Please use the Barid portal.'
        }
    
    def cancel_shipment(self, tracking_number):
        """
        Cancel a shipment.
        Note: Check if Barid API supports cancellation.
        
        Args:
            tracking_number: The package tracking number
            
        Returns:
            dict: Cancellation result or error
        """
        # TODO: Implement when Barid provides cancellation endpoint
        _logger.warning("Barid cancellation API not yet implemented")
        return {
            'success': False,
            'error': 'Shipment cancellation not available via API. Please contact Barid directly.'
        }


# Provider registry - for factory pattern
PROVIDER_CLASS = BaridProvider
