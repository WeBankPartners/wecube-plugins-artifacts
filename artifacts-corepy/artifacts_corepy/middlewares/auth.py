# coding=utf-8

from __future__ import absolute_import

import base64
import binascii
import jwt
import jwt.exceptions
from talos.core import config
from talos.core import exceptions as base_ex

CONF = config.CONF


def decode_key(key):
    new_key = key
    max_padding = 3
    while max_padding > 0:
        try:
            return base64.b64decode(new_key)
        except binascii.Error as e:
            new_key += '='
            max_padding -= 1
            if max_padding <= 0:
                raise e


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
                token_info = jwt.decode(token, key=decode_key(secret), verify=verify_token)
                req.auth_user = token_info['sub']
            except jwt.exceptions.ExpiredSignatureError as e:
                raise base_ex.AuthError()
            except jwt.exceptions.DecodeError as e:
                raise base_ex.AuthError()
        else:
            raise base_ex.AuthError()
