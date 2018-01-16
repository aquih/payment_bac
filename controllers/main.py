# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BACController(http.Controller):
    _return_url = '/payment/bac/return'

    @http.route([
        '/payment/bac/return',
    ], type='http', auth='none', csrf=False)
    def bac_return(self, **post):
        """ BAC """
        _logger.info('BAC: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'bac')
        post = dict((key.upper(), value) for key, value in post.items())
        return_url = post.get('ADD_RETURNDATA') or '/'
        return werkzeug.utils.redirect(return_url)
