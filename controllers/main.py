# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class BACController(http.Controller):
    _return_url = '/payment/bac/return'

    @http.route([
        '/payment/bac/return',
    ], type='http', auth='none')
    def bac_return(self, **post):
        """ BAC """
        _logger.info('BAC: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'bac', context=request.context)
        _logger.warn(post)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
