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
            'key_id': self.bac_key_id,
            'bac_amount': values['amount'],
            'bac_reference': values['reference'],
            'bac_return': '%s' % urlparse.urljoin(base_url, BACController._return_url),
        })
        return bac_tx_values

    @api.multi
    def bac_get_form_action_url(self):
        return "https://credomatic.compassmerchantsolutions.com/cart/cart.php"


# class TxBAC(models.Model):
#     _inherit = 'payment.transaction'
#
#     # bac status
#     _bac_valid_tx_status = [190]
#     _bac_pending_tx_status = [790, 791, 792, 793]
#     _bac_cancel_tx_status = [890, 891]
#     _bac_error_tx_status = [490, 491, 492]
#     _bac_reject_tx_status = [690]
#
#     # --------------------------------------------------
#     # FORM RELATED METHODS
#     # --------------------------------------------------
#
#     @api.model
#     def _bac_form_get_tx_from_data(self, data):
#         """ Given a data dict coming from bac, verify it and find the related
#         transaction record. """
#         origin_data = dict(data)
#         data = normalize_keys_upper(data)
#         reference, pay_id, shasign = data.get('BRQ_INVOICENUMBER'), data.get('BRQ_PAYMENT'), data.get('BRQ_SIGNATURE')
#         if not reference or not pay_id or not shasign:
#             error_msg = _('BAC: received data with missing reference (%s) or pay_id (%s) or shasign (%s)') % (reference, pay_id, shasign)
#             _logger.info(error_msg)
#             raise ValidationError(error_msg)
#
#         tx = self.search([('reference', '=', reference)])
#         if not tx or len(tx) > 1:
#             error_msg = _('BAC: received data for reference %s') % (reference)
#             if not tx:
#                 error_msg += _('; no order found')
#             else:
#                 error_msg += _('; multiple order found')
#             _logger.info(error_msg)
#             raise ValidationError(error_msg)
#
#         # verify shasign
#         shasign_check = tx.acquirer_id._bac_generate_digital_sign('out', origin_data)
#         if shasign_check.upper() != shasign.upper():
#             error_msg = _('BAC: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data)
#             _logger.info(error_msg)
#             raise ValidationError(error_msg)
#
#         return tx
#
#     def _bac_form_get_invalid_parameters(self, data):
#         invalid_parameters = []
#         data = normalize_keys_upper(data)
#         if self.acquirer_reference and data.get('BRQ_TRANSACTIONS') != self.acquirer_reference:
#             invalid_parameters.append(('Transaction Id', data.get('BRQ_TRANSACTIONS'), self.acquirer_reference))
#         # check what is buyed
#         if float_compare(float(data.get('BRQ_AMOUNT', '0.0')), self.amount, 2) != 0:
#             invalid_parameters.append(('Amount', data.get('BRQ_AMOUNT'), '%.2f' % self.amount))
#         if data.get('BRQ_CURRENCY') != self.currency_id.name:
#             invalid_parameters.append(('Currency', data.get('BRQ_CURRENCY'), self.currency_id.name))
#
#         return invalid_parameters
#
#     def _bac_form_validate(self, data):
#         data = normalize_keys_upper(data)
#         status_code = int(data.get('BRQ_STATUSCODE', '0'))
#         if status_code in self._bac_valid_tx_status:
#             self.write({
#                 'state': 'done',
#                 'acquirer_reference': data.get('BRQ_TRANSACTIONS'),
#             })
#             return True
#         elif status_code in self._bac_pending_tx_status:
#             self.write({
#                 'state': 'pending',
#                 'acquirer_reference': data.get('BRQ_TRANSACTIONS'),
#             })
#             return True
#         elif status_code in self._bac_cancel_tx_status:
#             self.write({
#                 'state': 'cancel',
#                 'acquirer_reference': data.get('BRQ_TRANSACTIONS'),
#             })
#             return True
#         else:
#             error = 'BAC: feedback error'
#             _logger.info(error)
#             self.write({
#                 'state': 'error',
#                 'state_message': error,
#                 'acquirer_reference': data.get('BRQ_TRANSACTIONS'),
#             })
#             return False
