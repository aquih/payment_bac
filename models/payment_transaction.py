# coding: utf-8
import logging
import hmac
import hashlib
import base64
import uuid

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_bac.controllers.payment import BACController
from odoo.tools.float_utils import float_compare
from odoo.http import request

_logger = logging.getLogger(__name__)

signed_field_names = ['access_key', 'profile_id', 'transaction_uuid', 'signed_field_names', 'unsigned_field_names', 'signed_date_time', 'locale', 'transaction_type', 'reference_number', 'amount', 'currency', 'ship_to_address_city']

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'bac':
            return res
        
        return_url = urls.url_join(self.acquirer_id.get_base_url(), BACController._return_url),
        session_id = request.session.sid
        reference = '{}|{}'.format(self.reference, request.session.sid)
        bac_partner_address1 = self.partner_id.street[0:35] if self.partner_id.street else ''
        bac_partner_address2 = self.partner_id.street2[0:35] if self.partner_id.street2 else ''
        
        to_hash = 'process_fixed|'+str(processing_values['amount'])+'|'+reference+'|'+self.acquirer_id.bac_key_text
        m = hashlib.md5(to_hash.encode('utf-8'))
        
        rendering_values = {
            'api_url': self.acquirer_id._bac_get_api_url(),
            'bac_key_id': self.acquirer_id.bac_key_id,
            'bac_key_text': self.acquirer_id.bac_key_text,
            'bac_amount': processing_values['amount'],
            'bac_reference': reference,
            'bac_return': '%s?session_id=x' %  return_url,
            'bac_hash': 'action|amount|order_description|'+m.hexdigest(),
            'bac_partner_first_name': self.partner_id.name,
            'bac_partner_last_name': '',
            'bac_partner_email': self.partner_id.email,
            'bac_partner_postal_code': self.partner_id.zip,
            'bac_partner_city': self.partner_id.city,
            'bac_partner_state': self.partner_id.state_id.code,
            'bac_partner_country': self.partner_id.country_id.code,
            'bac_partner_phone': self.partner_id.phone,
            'bac_partner_address1': bac_partner_address1,
            'bac_partner_address2': bac_partner_address2,
        }
        return rendering_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'bac':
            return tx
        
        complete_reference = data.get('order_description', '')
        reference_parts = complete_reference.split('|')
        reference = reference_parts[0]
        if not reference:
            error_msg = _('BAC: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference), ('provider', '=', 'bac')])
        _logger.info(tx)

        if not tx or len(tx) > 1:
            error_msg = _('BAC: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple orders found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'bac':
            return
        
        complete_reference = data.get('order_description', '')
        reference_parts = complete_reference.split('|')
        reference = reference_parts[0]
        
        self.acquirer_reference = reference
        status_code = data.get('response', '3')
        if status_code == '1':
            self._set_done()
        else:
            error = 'BAC: error '+data.get('message')
            _logger.info(error)
            self._set_error(_("Your payment was refused (code %s). Please try again.", status_code))
