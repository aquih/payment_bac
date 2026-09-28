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
    def bac_return(self, **raw_data):
        """ Process the data returned by BAC after redirection.

        :param dict raw_data: The feedback data
        """

        if raw_data:
            _logger.info("handling redirection from BAC with data:\n%s", pprint.pformat(raw_data))
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('bac', raw_data)
            tx_sudo._process('bac', raw_data)
        
        return request.redirect('/payment/status')
