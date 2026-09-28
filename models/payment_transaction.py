# coding: utf-8
import logging
import hashlib

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_bac.controllers.payment import BACController
from odoo.addons.payment_bac import const

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if processing_values['provider_code'] != 'bac':
            return res
        
        return_url = urls.url_join(self.provider_id.get_base_url(), BACController._return_url)
        reference = self.reference
        bac_partner_address1 = self.partner_id.street[0:35] if self.partner_id.street else ''
        bac_partner_address2 = self.partner_id.street2[0:35] if self.partner_id.street2 else ''
        
        to_hash = 'process_fixed|'+str(processing_values['amount'])+'|'+reference+'|'+self.provider_id.bac_key_text
        m = hashlib.md5(to_hash.encode('utf-8'))
        
        rendering_values = {
            'api_url': self.provider_id._bac_get_api_url(),
            'bac_key_id': self.provider_id.bac_key_id,
            'bac_key_text': self.provider_id.bac_key_text,
            'bac_amount': processing_values['amount'],
            'bac_reference': reference,
            'bac_return': return_url,
            'bac_hash': 'action|amount|order_description|'+m.hexdigest(),
            'bac_partner_first_name': self.partner_id.name,
            'bac_partner_last_name': '',
            'bac_partner_email': self.partner_id.email,
            'bac_partner_postal_code': self.partner_id.zip,
            'bac_partner_city': self.partner_id.city,
            'bac_partner_state': self.partner_id.state_id.name,
            'bac_partner_country': self.partner_id.country_id.code,
            'bac_partner_phone': self.partner_id.phone,
            'bac_partner_address1': bac_partner_address1,
            'bac_partner_address2': bac_partner_address2,
        }
        return rendering_values

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        if provider_code != 'bac':
            return super()._extract_reference(provider_code, payment_data)

        return payment_data.get('order_description')

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'bac':
            return super()._extract_amount_data(payment_data)

        amount = payment_data.get('amount')
        currency_code = 'GTQ'
        return {
            'amount': float(amount),
            'currency_code': currency_code,
        }

    def _apply_updates(self, payment_data):
        if self.provider_code != 'bac':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = payment_data.get('transactionid')

        # Update the payment method.
        payment_method_code = '001'
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment payment_data.
        status_code = payment_data.get('response', '3')
        if status_code in const.STATUS_CODES_MAPPING['done']:
            self._set_done()
        elif status_code in const.STATUS_CODES_MAPPING['refused']:
            self._set_error("Su pago fue rechazado (code %s). Por favor intente de nuevo.", status_code)
        elif status_code in const.STATUS_CODES_MAPPING['error']:
            self._set_error(
                "Ocurrio un error al procesar su pago (code %s). Por favor intente de nuevo.",
                status_code,
            )
        else:
            _logger.warning(
                "Datos invalidos en la decision (%s) para la transaccion %s.",
                status_code, self.reference
            )
            self._set_error(_("Decision invalida: %s.", status_code))