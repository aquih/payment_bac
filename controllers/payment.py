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

    @http.route(['/payment/bac/return'], type='http', auth='public', csrf=False)
    def bac_return(self, **data):
        """ Process the data returned by BAC after redirection.

        :param dict data: The feedback data
        """
        _logger.info('BAC: entering _handle_feedback_data with post data %s', pprint.pformat(data))  # debug
        request.env['payment.transaction'].sudo()._handle_feedback_data('bac', data)
        #  request.redirect('/payment/status')

        response_return_url = data.pop('return_url', '/payment/status')

        headers = {
            'Location': response_return_url,
        }
                
        response = Response(response_return_url, status=302, headers=headers)
        if data.get('order_description'):
            complete_reference = data.get('order_description')
            reference_parts = complete_reference.split('|')
            session_id = reference_parts[1]
            #_logger.warn('req session_id: {}'.format(session_id))
            #_logger.warn('current session_id: {}'.format(request.session.sid))
            if session_id != request.session.sid:
                #_logger.warn('setting session_id: {}'.format(session_id))
                response.set_cookie('session_id', session_id, max_age=90 * 24 * 60 * 60, httponly=True)

        return response
