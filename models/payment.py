# coding: utf-8
import logging
import urllib
import random
import hmac
import hashlib
import base64
import uuid

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_bac.controllers.payment import BACController
from odoo.tools.float_utils import float_compare
from odoo.release import version_info

_logger = logging.getLogger(__name__)

class AcquirerBAC(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('bac', 'BAC')])
    bac_key_id = fields.Char('Key ID', required_if_provider='bac', groups='base.group_user')
    bac_key_text = fields.Char('Key Text', required_if_provider='bac', groups='base.group_user')

    def bac_form_generate_values(self, values):
        reference = values['reference']
        to_hash = 'process_fixed|'+str(values['amount'])+'|'+reference+'|'+self.bac_key_text
        m = hashlib.md5(to_hash.encode('utf-8'))
        
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        bac_tx_values = dict(values)
        bac_tx_values.update({
            'bac_key_id': self.bac_key_id,
            'bac_key_text': self.bac_key_text,
            'bac_amount': values['amount'],
            'bac_reference': reference,
            'bac_return': '%s' %  urllib.parse.urljoin(base_url, BACController._return_url),
            'bac_hash': 'action|amount|order_description|'+m.hexdigest(),
        })
        return bac_tx_values

    def bac_get_form_action_url(self):
        self.ensure_one()
        return "https://credomatic.compassmerchantsolutions.com/cart/cart.php"

class TxBAC(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _bac_form_get_tx_from_data(self, data):
        """ Given a data dict coming from bac, verify it and find the related
        transaction record. """
        reference = data.get('order_description')
        if not reference:
            error_msg = _('BAC: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        
        if version_info[0] == 11:
            if tx.sale_order_id:
                data['return_url'] = '/quote/%d/%s' % (tx.sale_order_id.id, tx.sale_order_id.access_token)
            else:
                data['return_url'] = '/my/invoices/%d?access_token=%s' % (tx.account_invoice_id.id, tx.account_invoice_id.access_token)

        if not tx or len(tx) > 1:
            error_msg = _('BAC: received data for reference %s') % (order)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _bac_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        status_code = data.get('response', '3')
        
        if status_code == '1':
            if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
                invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))

        return invalid_parameters

    def _bac_form_validate(self, data):
        status_code = data.get('response', '3')
        vals = {
            "acquirer_reference": data.get('transaction_id'),
        }
        if status_code == '1':
            if version_info[0] > 11:
                self.write(vals)
                self._set_transaction_done()
            else:
                vals['state'] = 'done'
                vals['date'] = fields.Datetime.now()
                self.write(vals)
            return True
        else:
            error = 'BAC: feedback error'
            _logger.info(error)
            if version_info[0] > 11:
                self.write(vals)
                self._set_transaction_error(error)
            else:
                vals['state'] = 'error'
                vals['state_message'] = error
                vals['date'] = fields.Datetime.now()
                self.write(vals)
            return False
