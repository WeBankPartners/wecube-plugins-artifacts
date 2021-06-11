# coding=utf-8
"""
artifacts_corepy.common.wecube
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目WeCube Client（Proxy）

"""
import logging

from artifacts_corepy.common import exceptions
from talos.core import config
from talos.core.i18n import _
from artifacts_corepy.common import utils

LOG = logging.getLogger(__name__)
CONF = config.CONF


class WeCubeClient(object):
    """WeCube Client"""
    def __init__(self, server, token):
        self.server = server.rstrip('/')
        self.token = token

    def build_headers(self):
        return {'Authorization': 'Bearer ' + self.token}

    def check_response(self, resp_json):
        if resp_json['status'] != 'OK':
            # 当创建/更新条目错误，且仅有一个错误时，返回内部错误信息
            if isinstance(resp_json.get('data', None), list) and len(resp_json['data']) == 1:
                if 'message' in resp_json['data'][0]:
                    raise exceptions.PluginError(message=resp_json['data'][0]['message'])
            raise exceptions.PluginError(message=resp_json['message'])

    def get(self, url, param=None):
        LOG.info('GET %s', url)
        LOG.debug('Request: query - %s, data - None', str(param))
        resp_json = utils.RestfulJson.get(url, headers=self.build_headers(), params=param)
        LOG.debug('Response: %s', str(resp_json))
        self.check_response(resp_json)
        return resp_json

    def post(self, url, data, param=None):
        LOG.info('POST %s', url)
        LOG.debug('Request: query - %s, data - %s', str(param), str(data))
        resp_json = utils.RestfulJson.post(url, headers=self.build_headers(), params=param, json=data)
        LOG.debug('Response: %s', str(resp_json))
        self.check_response(resp_json)
        return resp_json

    def update(self, url_path, data):
        url = self.server + url_path
        return self.post(url, data)

    def retrieve(self, url_path):
        url = self.server + url_path
        return self.post(url, {})
