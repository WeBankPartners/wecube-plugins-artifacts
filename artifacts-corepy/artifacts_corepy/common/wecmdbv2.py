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

URL_PREFIX = '/wecmdb/api/v1'


class WeCMDBClient(object):
    """WeCMDB Client"""
    def __init__(self, server, token):
        self.server = server.rstrip('/')
        self.token = token

    @staticmethod
    def build_retrieve_url(citype):
        return URL_PREFIX + '/ci-data/query/%s' % citype

    @staticmethod
    def build_create_url(citype):
        return URL_PREFIX + '/ci-data/do/Add/%s' % citype

    def build_update_url(self, citype):
        # TODO: fix Update to state machine
        return URL_PREFIX + '/ci-data/do/Update/%s' % citype

    @staticmethod
    def build_delete_url(citype):
        return URL_PREFIX + '/ci-data/do/Delete/%s' % citype

    @staticmethod
    def build_confirm_url(citype):
        return URL_PREFIX + '/ci-data/do/Confirm/%s' % citype

    @staticmethod
    def build_view_data_url():
        return URL_PREFIX + '/view-data'

    @staticmethod
    def build_citype_url():
        return URL_PREFIX + '/ci-types'

    @staticmethod
    def build_citype_refs_url(citype):
        return URL_PREFIX + '/ci-types/references/%s' % citype

    @staticmethod
    def build_citype_attrs_url(citype):
        return URL_PREFIX + '/ci-types-attr/%s/attributes' % citype

    @staticmethod
    def build_state_operation_url(operation, citype):
        return URL_PREFIX + '/ci-data/do/%s/%s' % (operation, citype)

    @staticmethod
    def build_enumcode_url(cat_id):
        return URL_PREFIX + '/base-key/categories/%s' % cat_id

    @staticmethod
    def build_ci_operation_url(citype):
        return URL_PREFIX + '/state-transition/%s' % citype

    @staticmethod
    def build_history_url(ci_guid):
        return URL_PREFIX + '/ci-data/rollback/query/%s' % ci_guid

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

    def format_item(self, data, keep_origin_value=None):
        new_data = {}
        for key, value in data.items():
            new_value = value
            if keep_origin_value and key in keep_origin_value:
                pass
            elif isinstance(value, (list, tuple, set)):
                if len(value) > 0:
                    if isinstance(value[0], dict):
                        new_value = ','.join([x['guid'] for x in value])
                    else:
                        new_value = ','.join(value)
                else:
                    new_value = ''
            elif isinstance(value, dict):
                new_value = value['guid']
            new_data[key] = new_value
        return new_data

    def format(self, data, keep_origin_value=None):
        if isinstance(data, (list, tuple, set)):
            return [self.format_item(item, keep_origin_value=keep_origin_value) for item in data]
        else:
            return self.format_item(data, keep_origin_value=keep_origin_value)

    def special_connector(self):
        return [{"code": "&\u0001", "value": "&"}, {"code": "\u0001=\u0001", "value": "="}]

    def history(self, ci_guid):
        url = self.server + self.build_history_url(ci_guid)
        return self.get(url)

    def citypes(self, data):
        url = self.server + self.build_citype_url()
        return self.get(url, data)

    def citype_refs(self, citype):
        url = self.server + self.build_citype_refs_url(citype)
        return self.get(url)

    def citype_attrs(self, citype):
        url = self.server + self.build_citype_attrs_url(citype)
        return self.get(url)

    def state_operation(self, operation, citype, data):
        # need citype in Add operation
        url = self.server + self.build_state_operation_url(operation, citype)
        return self.post(url, self.format(data))

    def enumcodes(self, cat_id):
        url = self.server + self.build_enumcode_url(cat_id)
        return self.get(url)

    def ci_operations(self, citype):
        url = self.server + self.build_ci_operation_url(citype)
        return self.get(url)

    def view_data(self, view_id, root_id, version):
        url = self.server + self.build_view_data_url()
        data = {"confirmTime": version, "rootCi": root_id, "viewId": view_id}
        return self.post(url, data)

    def create(self, citype, data):
        url = self.server + self.build_create_url(citype)
        return self.post(url, data)

    def update(self, citype, data, keep_origin_value=None):
        url = self.server + self.build_update_url(citype)
        return self.post(url, self.format(data, keep_origin_value=keep_origin_value))

    def retrieve(self, citype, query):
        url = self.server + self.build_retrieve_url(citype)
        return self.post(url, query)

    def delete(self, citype, data):
        url = self.server + self.build_delete_url(citype)
        return self.post(url, data)

    def confirm(self, citype, data):
        url = self.server + self.build_confirm_url(citype)
        return self.post(url, data)