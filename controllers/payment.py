# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug
from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class BACController(http.Controller):
    _return_url = '/payment/bac/return'

    @http.route(['/payment/bac/return'], type='http', auth='public', csrf=False, save_session=False)
    def bac_return(self, **data):
        """ Process the data returned by BAC after redirection.

        :param dict data: The feedback data
        """
        if data:
            _logger.info('BAC: entering _handle_feedback_data with post data %s', pprint.pformat(data))  # debug
            request.env['payment.transaction'].sudo()._handle_feedback_data('bac', data)
        
        return request.redirect('/payment/status')
