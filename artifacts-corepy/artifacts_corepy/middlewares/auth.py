# coding=utf-8

from __future__ import absolute_import

import jwt
import jwt.exceptions
from artifacts_corepy.common import utils
from talos.core import config
from talos.core import exceptions as base_ex

CONF = config.CONF


class JWTAuth(object):
    """中间件，提供JWT Token信息解析"""
    def process_request(self, req, resp):
        token_header = req.headers.get('Authorization'.upper(), None)
        secret = CONF.jwt_signing_key
        if token_header:
            token = token_header[len('Bearer '):]
            req.auth_token = token
            verify_token = False
            if secret:
                verify_token = True
            try:
                token_info = jwt.decode(token, key=utils.b64decode_key(secret), verify=verify_token)
                req.auth_user = token_info['sub']
            except jwt.exceptions.ExpiredSignatureError as e:
                raise base_ex.AuthError()
            except jwt.exceptions.DecodeError as e:
                raise base_ex.AuthError()
        else:
            raise base_ex.AuthError()
