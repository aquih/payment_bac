# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BACController(http.Controller):
    _return_url = '/payment/bac/return'

    @http.route(['/payment/bac/return'], type='http', auth='public', csrf=False)
    def bac_return(self, **post):
        """ BAC """
        _logger.info('BAC: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'bac')
        _logger.warn(post)
        
        response_return_url = post.pop('return_url', '/payment/process')

        headers = {
            'Location': response_return_url,
            #'X-Openerp-Session-Id': 'eb89202cb7b73e3653cc3952ea54336a993422d6',
        }
                
        response = Response(response_return_url, status=302, headers=headers)
        if post.get('order_description'):
            complete_reference = post.get('order_description')
            reference_parts = complete_reference.split('|')
            session_id = reference_parts[1]
            _logger.warn('req session_id: {}'.format(session_id))
            _logger.warn('current session_id: {}'.format(request.session.sid))
            if session_id != request.session.sid:
                _logger.warn('setting session_id: {}'.format(session_id))
                response.set_cookie('session_id', session_id, max_age=90 * 24 * 60 * 60, httponly=True)

        return response
