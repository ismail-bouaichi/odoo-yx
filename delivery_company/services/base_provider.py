# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Abstract base class for delivery providers.
All providers must implement these methods.
"""

from abc import ABC, abstractmethod
import logging

_logger = logging.getLogger(__name__)


class BaseDeliveryProvider(ABC):
    """
    Abstract base class that defines the contract ALL providers must follow.
    
    Each provider (Barid, Ozon, etc.) must inherit from this class
    and implement all abstract methods.
    
    Usage:
        provider = BaridProvider(delivery_company_record)
        result = provider.track_package('ANP03920060MA')
    """
    
    def __init__(self, company_record):
        """
        Initialize provider with delivery.company record.
        
        :param company_record: delivery.company recordset from Odoo
        """
        self.company = company_record
        self._validate_credentials()
    
    @property
    @abstractmethod
    def provider_code(self):
        """Unique identifier for this provider (e.g., 'barid', 'ozon')"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self):
        """Human-readable name (e.g., 'Barid Al-Maghrib')"""
        pass
    
    @abstractmethod
    def _validate_credentials(self):
        """
        Validate that required credentials are configured.
        Should raise UserError if credentials are missing.
        """
        pass
    
    @abstractmethod
    def test_connection(self):
        """
        Test API connectivity.
        
        :return: {
            'success': bool,
            'message': str,
            'details': dict (optional)
        }
        """
        pass
    
    @abstractmethod
    def track_package(self, tracking_number):
        """
        Get tracking information for a package.
        
        :param tracking_number: The shipment tracking number
        :return: {
            'success': bool,
            'tracking_number': str,
            'status': str,
            'events': list,
            'raw_response': any
        }
        """
        pass
    
    @abstractmethod
    def create_shipment(self, shipment_data):
        """
        Create a new shipment.
        
        :param shipment_data: Dict with shipment details (sender, recipient, etc.)
        :return: {
            'success': bool,
            'shipment_id': str,
            'tracking_number': str,
            'label_url': str (optional),
            'raw_response': any
        }
        """
        pass
    
    @abstractmethod
    def get_label(self, shipment_id):
        """
        Get shipping label (usually PDF).
        
        :param shipment_id: The shipment ID from create_shipment
        :return: Raw label data (PDF bytes)
        """
        pass
    
    def cancel_shipment(self, shipment_id):
        """
        Cancel a shipment.
        Default: Not supported. Override in provider if available.
        
        :param shipment_id: The shipment ID to cancel
        :return: {'success': bool, 'message': str}
        """
        return {
            'success': False,
            'message': f'{self.provider_name} does not support shipment cancellation',
        }
