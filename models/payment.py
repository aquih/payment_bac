# coding: utf-8
from hashlib import sha1
import logging
import urllib
import urlparse
import random
import hashlib

from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.addons.payment_bac.controllers.main import BACController
from openerp.osv import osv, fields
from openerp.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

class AcquirerBAC(osv.Model):
    _inherit = 'payment.acquirer'

    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerBAC, self)._get_providers(cr, uid, context=context)
        providers.append(['bac', 'BAC'])
        return providers

    _columns = {
        'bac_key_id': fields.char('Key ID', required_if_provider='bac', groups='base.group_user'),
        'bac_key_text': fields.char('Key Text', required_if_provider='bac', groups='base.group_user'),
    }

    def bac_form_generate_values(self, cr, uid, id, partner_values, values, context=None):
        # reference = values['reference']+'--{:04d}'.format(random.randint(1, 100))
        reference = values['reference']
        m = hashlib.md5('process_fixed|'+str(values['amount'])+'|'+reference+'|'+self.bac_key_text)
        base_url = self.pool['ir.config_parameter'].get_param(cr, uid, 'web.base.url')
        bac_tx_values = dict(values)
        bac_tx_values.update({
            'bac_key_id': self.bac_key_id,
            'bac_key_text': self.bac_key_text,
            'bac_amount': values['amount'],
            'bac_reference': reference,
            'bac_return': '%s' % urlparse.urljoin(base_url, BACController._return_url),
            'bac_hash': 'action|amount|order_description|'+m.hexdigest(),
        })
        logging.warn(bac_tx_values)
        return partner_values, bac_tx_values

    def bac_get_form_action_url(self, cr, uid, id, context=None):
        return "https://credomatic.compassmerchantsolutions.com/cart/cart.php"

class TxBAC(osv.Model):
    _inherit = 'payment.transaction'

    _columns = {
         'bac_txnid': fields.char('Transaction ID'),
    }

    def _bac_form_get_tx_from_data(self, cr, uid, data, context=None):
        """ Given a data dict coming from bac, verify it and find the related
        transaction record. """
        origin_data = dict(data)
        reference = data.get('order_description')
        if not reference:
            error_msg = _('BAC: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # order = reference.split('--')[0]
        order = reference
        tx_ids = self.search(cr, uid, [('reference', '=', reference)], context=context)
        if not tx_ids or len(tx_ids) > 1:
            error_msg = _('BAC: received data for reference %s') % (order)
            if not tx_ids:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        tx = self.pool['payment.transaction'].browse(cr, uid, tx_ids[0], context=context)

        return tx

    def _bac_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        invalid_parameters = []
        # check what is buyed
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('amount'), '%.2f' % self.amount))

        return invalid_parameters

    def _bac_form_validate(self, cr, uid, tx, data, context=None):
        status_code = data.get('response', '3')
        if status_code == '1':
            tx.write({
                'state': 'done',
                'bac_txnid': data.get('transactionid'),
            })
            return True
        else:
            error = 'BAC: feedback error'
            _logger.info(error)
            tx.write({
                'state': 'error',
                'state_message': error,
                'bac_txnid': data.get('transactionid'),
            })
            return False
