# coding=utf-8
"""
artifacts_corepy.common.wecmdb
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目WeCMDB Client

"""
import logging

from artifacts_corepy.common import exceptions
from talos.core import config
from talos.core.i18n import _
from artifacts_corepy.common import utils

LOG = logging.getLogger(__name__)
CONF = config.CONF


class WeCMDBClient(object):
    """WeCMDB Client"""
    def __init__(self, server, token):
        self.server = server.rstrip('/')
        self.token = token

    @staticmethod
    def build_retrieve_url(citype):
        return '/wecmdb/api/v2/ci/%s/retrieve' % citype

    @staticmethod
    def build_create_url(citype):
        return '/wecmdb/api/v2/ci/%s/create' % citype

    @staticmethod
    def build_update_url(citype):
        return '/wecmdb/api/v2/ci/%s/update' % citype

    @staticmethod
    def build_version_tree_url(citype_from, citype_to, version):
        return '/wecmdb/api/v2/ci/from/%d/to/%d/versions/%s/retrieve' % (citype_from, citype_to, version)

    @staticmethod
    def build_connector_url():
        return '/wecmdb/api/v2/static-data/special-connector'

    @staticmethod
    def build_citype_url():
        return '/wecmdb/api/v2/ciTypes/retrieve'

    @staticmethod
    def build_enumcode_url():
        return '/wecmdb/api/v2/enum/codes/retrieve'

    def build_headers(self):
        return {'Authorization': 'Bearer ' + self.token}

    def check_response(self, resp_json):
        if resp_json['statusCode'] != 'OK':
            # 当创建/更新条目错误，且仅有一个错误时，返回内部错误信息
            if isinstance(resp_json.get('data', None), list) and len(resp_json['data']) == 1:
                if 'errorMessage' in resp_json['data'][0]:
                    raise exceptions.PluginError(message=resp_json['data'][0]['errorMessage'])
            raise exceptions.PluginError(message=resp_json['statusMessage'])

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

    def special_connector(self):
        url = self.server + self.build_connector_url()
        return self.get(url)

    def citypes(self, data):
        url = self.server + self.build_citype_url()
        return self.post(url, data)

    def enumcodes(self, data):
        url = self.server + self.build_enumcode_url()
        return self.post(url, data)

    def version_tree(self, citype_from, citype_to, version, query):
        url = self.server + self.build_version_tree_url(citype_from, citype_to, version)
        return self.post(url, query)

    def create(self, citype, data):
        url = self.server + self.build_create_url(citype)
        return self.post(url, data)

    def update(self, citype, data):
        url = self.server + self.build_update_url(citype)
        return self.post(url, data)

    def retrieve(self, citype, query):
        url = self.server + self.build_retrieve_url(citype)
        return self.post(url, query)
