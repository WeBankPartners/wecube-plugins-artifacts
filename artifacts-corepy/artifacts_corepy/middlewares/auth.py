# coding=utf-8

from __future__ import absolute_import

import jwt


class JWTAuth(object):
    """中间件，提供JWT Token信息解析"""
    def process_request(self, req, resp):
        token_header = req.headers.get('Authorization'.upper(), None)
        if token_header:
            token = token_header[len('Bearer '):]
            token_info = jwt.decode(token, key='', verify=False)
            req.auth_user = token_info['sub']
