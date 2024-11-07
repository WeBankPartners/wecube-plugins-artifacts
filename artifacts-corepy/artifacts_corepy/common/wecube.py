# coding=utf-8
"""
artifacts_corepy.common.wecube
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目WeCube Client（Proxy）

"""
import base64
import logging
import random

from talos.core import config
from talos.core.i18n import _
from artifacts_corepy.common import utils

LOG = logging.getLogger(__name__)
CONF = config.CONF


def encrypt(message, rsa_key):
    import M2Crypto.RSA
    template = '''-----BEGIN PRIVATE KEY-----
%s
-----END PRIVATE KEY-----'''
    key_pem = template % rsa_key
    privat_key = M2Crypto.RSA.load_key_string(key_pem.encode())
    ciphertext = privat_key.private_encrypt(message.encode(), M2Crypto.RSA.pkcs1_padding)
    encrypted_message = base64.b64encode(ciphertext).decode()
    return encrypted_message


class WeCubeClient(utils.ClientMixin):
    """WeCube Client"""
    def __init__(self, server, token):
        self.server = server.rstrip('/')
        self.token = token

    def login_subsystem(self, set_self=True):
        '''client = WeCubeClient('http://ip:port', None)
           token = client.login_subsystem()
           # use your access token
        '''
        sequence = 'abcdefghijklmnopqrstuvwxyz1234567890'
        nonce = ''.join(random.choices(sequence, k=4))
        url = self.server + '/auth/v1/api/login'
        password = encrypt('%s:%s' % (CONF.wecube.sub_system_code, nonce), CONF.wecube.sub_system_key)
        data = {
            "password": password,
            "username": CONF.wecube.sub_system_code,
            "nonce": nonce,
            "clientType": "SUB_SYSTEM"
        }
        resp_json = self.post(url, data)
        for token in resp_json['data']:
            if token['tokenType'] == 'accessToken':
                if set_self:
                    self.token = token['token']
                return token['token']

    def update(self, url_path, data):
        url = self.server + url_path
        return self.post(url, data)

    def get(self, url_path, param=None):
        url = self.server + url_path
        return super().get(url, param)

    def retrieve(self, url_path, data=None):
        # op：eq-等于；neq-不等于；in-范围过滤；like-模糊过滤；gt-大于；lt-小于；is - NULL ； isnot - NULL；  
        # {
        #     "criteria": {
        #             "attrName": "id",
        #             "condition": "0001_274321635"
        #     },
        #     "additionalFilters": [{
        #             "attrName": "att1",
        #             "op": "eq",
        #             "condition": "eee dddd"
        #     }, {
        #             "attrName": "att2",
        #             "op": "in",
        #             "condition": ["asfdd", "bsf"]
        #     }]
        # }
        url = self.server + url_path
        return self.post(url, data or {})
