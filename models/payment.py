# coding: utf-8
from hashlib import sha1
import logging
import urllib
import urlparse

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_bac.controllers.main import BACController
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

class AcquirerBAC(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('bac', 'BAC')])
    bac_key_id = fields.Char('Key ID', required_if_provider='bac', groups='base.group_user')

    @api.multi
    def bac_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        bac_tx_values = dict(values)
        bac_tx_values.update({
            'bac_key_id': self.bac_key_id,
            'bac_amount': values['amount'],
            'bac_reference': values['reference'],
            'bac_return': '%s' % urlparse.urljoin(base_url, BACController._return_url),
        })
        return bac_tx_values

    @api.multi
    def bac_get_form_action_url(self):
        return "https://credomatic.compassmerchantsolutions.com/cart/cart.php"

class TxBAC(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _bac_form_get_tx_from_data(self, data):
        """ Given a data dict coming from bac, verify it and find the related
        transaction record. """
        origin_data = dict(data)
        reference = data.get('order_description')
        if not reference:
            error_msg = _('BAC: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('BAC: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _bac_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        # check what is buyed
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('amount'), '%.2f' % self.amount))

        return invalid_parameters

    def _bac_form_validate(self, data):
        status_code = data.get('responsetext', '--')
        if status_code == 'SUCCESS':
            self.write({
                'state': 'done',
                'acquirer_reference': data.get('transactionid'),
            })
            return True
        else:
            error = 'BAC: feedback error'
            _logger.info(error)
            self.write({
                'state': 'error',
                'state_message': error,
                'acquirer_reference': data.get('transactionid'),
            })
            return False
