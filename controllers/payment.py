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
        return werkzeug.utils.redirect(post.pop('return_url', '/payment/process'))
