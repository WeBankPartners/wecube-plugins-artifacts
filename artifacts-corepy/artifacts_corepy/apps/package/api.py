# coding=utf-8

from __future__ import absolute_import

import datetime
import hashlib
from logging import root
import os
import logging
import collections
import re
import shutil
import tempfile
import os.path
from talos.core import config
from talos.utils import http
from talos.core import utils
from talos.db import crud
from talos.db import converter
from talos.core.i18n import _
from talos.utils import scoped_globals

from artifacts_corepy.common import exceptions
from artifacts_corepy.common import nexus
from artifacts_corepy.common import s3
from artifacts_corepy.common import wecmdb
from artifacts_corepy.common import utils as artifact_utils

LOG = logging.getLogger(__name__)
CONF = config.CONF


def is_upload_local_enabled():
    return utils.bool_from_string(CONF.wecube.upload_enabled)


def is_upload_nexus_enabled():
    return utils.bool_from_string(CONF.wecube.upload_nexus_enabled)


def calculate_md5(fileobj):
    m = hashlib.md5()
    chunk_size = 64 * 1024
    fileobj.seek(0)
    chunk = fileobj.read(chunk_size)
    while chunk:
        m.update(chunk)
        chunk = fileobj.read(chunk_size)
    return m.hexdigest()


def calculate_file_md5(filepath):
    with open(filepath, 'rb') as fileobj:
        return calculate_md5(fileobj)


class FileNameConcater(converter.NullConverter):
    def convert(self, value):
        return '|'.join([i.get('filename') for i in value if i.get('filename')])


class BooleanNomalizedConverter(converter.NullConverter):
    def __init__(self, default=False):
        self.fallback_value = default

    def convert(self, value):
        return 'true' if utils.bool_from_string(value, default=self.fallback_value) else 'false'


class WeCubeResource(object):
    def __init__(self, server=None, token=None):
        self.server = server or CONF.wecube.server
        self.token = token or scoped_globals.GLOBALS.request.auth_token

    def get_cmdb_client(self):
        return wecmdb.WeCMDBClient(self.server, self.token)

    def list(self, params):
        pass

    def list_by_post(self, filters):
        pass


class SystemDesign(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "showCiHistory": True
            },
            "filters": [{
                "name": "fixed_date",
                "operator": "notNull",
                "value": None
            }, {
                "name": "fixed_date",
                "operator": "ne",
                "value": ""
            }],
            "paging":
            False,
            "sorting": {
                "asc": False,
                "field": "fixed_date"
            }
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.system_design, query)
        last_version = collections.OrderedDict()
        for content in resp_json['data']['contents']:
            r_guid = content['data']['r_guid']
            if (r_guid not in last_version):
                last_version[r_guid] = content
        return {
            'contents': list(last_version.values()),
            'pageInfo': None,
        }

    def get(self, rid):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "showCiHistory": True
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": rid
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.system_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") % {'rid': rid})
        fixed_date = resp_json['data']['contents'][0]['data']['fixed_date']
        results = []
        if fixed_date:
            query = {"dialect": {"showCiHistory": False}, "filters": [], "paging": False}
            resp_json = cmdb_client.version_tree(CONF.wecube.wecmdb.citypes.system_design,
                                                 CONF.wecube.wecmdb.citypes.unit_design, fixed_date, query)
            for i in resp_json['data']:
                if rid == i.get('data', {}).get('guid', None):
                    results.append(i)
        return results


class SpecialConnector(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.special_connector()
        return resp_json['data']


class CiTypes(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        with_attributes = utils.bool_from_string(params.get('with-attributes', 'no'))
        status = params.get('status', '').split(',')
        query = {"filters": [], "paging": False, "refResources": [], "sorting": {"asc": True, "field": "seqNo"}}
        if status:
            query['filters'].append({"name": "status", "operator": "in", "value": status})
        if with_attributes:
            query['refResources'].append('attributes')
            if status:
                query['filters'].append({"name": "attributes.status", "operator": "in", "value": status})
        resp_json = cmdb_client.citypes(query)
        return resp_json['data']['contents']

    def get_references(self, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "showCiHistory": False
            },
            "filters": [{
                "name": "referenceId",
                "operator": "eq",
                "value": ci_type_id
            }, {
                "name": "inputType",
                "operator": "in",
                "value": ["ref", "multiRef"]
            }],
            "paging":
            False,
            "refResources": ["ciType"]
        }
        resp_json = cmdb_client.citype_attrs(query)
        return resp_json['data']['contents']

    def get_attributes(self, accept_types, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "showCiHistory": False
            },
            "filters": [{
                "name": "ciTypeId",
                "operator": "eq",
                "value": ci_type_id
            }],
            "paging": False,
            "sorting": {
                "asc": True,
                "field": "displaySeqNo"
            }
        }
        if accept_types:
            query['filters'].append({"name": "inputType", "operator": "in", "value": accept_types})
        resp_json = cmdb_client.citype_attrs(query)
        return resp_json['data']['contents']

    def update_state(self, data, operation):
        cmdb_client = self.get_cmdb_client()
        result = cmdb_client.state_operation(operation, data)
        return result['data']

    def batch_delete(self, data, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        result = cmdb_client.delete(ci_type_id, data)
        return result['data']


class EnumCodes(WeCubeResource):
    def list_by_post(self, query):
        cmdb_client = self.get_cmdb_client()
        query.setdefault('filters', [])
        query.setdefault('paging', False)
        query.setdefault('refResources', [])
        query['filters'].append({"name": "cat.catType", "operator": "eq", "value": 1})
        query['refResources'].append('cat')
        query['refResources'].append('cat.catType')
        resp_json = cmdb_client.enumcodes(query)
        return resp_json['data']


class UnitDesignPackages(WeCubeResource):
    def list_by_post(self, query, unit_design_id):
        cmdb_client = self.get_cmdb_client()
        query.setdefault('filters', [])
        query.setdefault('paging', False)
        query['filters'].append({"name": "unit_design", "operator": "eq", "value": unit_design_id})
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        for i in resp_json['data']['contents']:
            i['data']['deploy_file_path'] = self.build_file_object(i['data']['deploy_file_path'])
            i['data']['start_file_path'] = self.build_file_object(i['data']['start_file_path'])
            i['data']['stop_file_path'] = self.build_file_object(i['data']['stop_file_path'])
            i['data']['diff_conf_file'] = self.build_file_object(i['data']['diff_conf_file'])
            # db部署支持
            fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                      'db_deploy_file_path')
            for field in fields:
                if field in i['data']:
                    i['data'][field] = self.build_file_object(i['data'][field])
        return resp_json['data']

    def build_file_object(self, filenames, spliter='|'):
        if not filenames:
            return []
        return [{
            'comparisonResult': None,
            'configKeyInfos': [],
            'filename': f,
            'isDir': None,
            'md5': None
        } for f in filenames.split(spliter)]

    def build_local_nexus_path(self, unit_design):
        return unit_design['data']['key_name']

    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design['data'].get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def download_url_parse(self, url):
        ret = {}
        results = url.split('/repository/', 1)
        ret['server'] = results[0]
        ret['fullpath'] = '/repository/' + results[1]
        results = results[1].split('/', 1)
        ret['repository'] = results[0]
        ret['filename'] = results[1].split('/')[-1]
        ret['group'] = '/' + results[1].rsplit('/', 1)[0]
        return ret

    def upload(self, filename, filetype, fileobj, unit_design_id):
        if not is_upload_local_enabled():
            raise exceptions.NotFoundError(message=_("Package uploading is disabled!"))
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": unit_design_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        nexus_server = None
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            nexus_server = CONF.wecube.nexus.server.rstrip('/')
            nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                             CONF.wecube.nexus.password)
            artifact_path = self.get_unit_design_artifact_path(unit_design)
        else:
            nexus_server = CONF.nexus.server.rstrip('/')
            nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
            artifact_path = self.build_local_nexus_path(unit_design)
        upload_result = nexus_client.upload(CONF.nexus.repository, artifact_path, filename, filetype, fileobj)
        new_download_url = upload_result['downloadUrl'].replace(nexus_server,
                                                                CONF.wecube.server.rstrip('/') + '/artifacts')
        package_rows = [{
            'name': filename,
            'deploy_package_url': new_download_url,
            'description': filename,
            'md5_value': calculate_md5(fileobj),
            'upload_user': scoped_globals.GLOBALS.request.auth_user,
            'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'unit_design': unit_design_id
        }]
        package_result = self.create(package_rows)
        return package_result['data']

    def upload_from_nexus(self, download_url, unit_design_id):
        if not is_upload_nexus_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": unit_design_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            # 更新unit_design.artifact_path && package.create 即上传成功
            url_info = self.download_url_parse(download_url)
            r_nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                               CONF.wecube.nexus.password)
            nexus_files = r_nexus_client.list(url_info['repository'], url_info['group'])
            nexus_md5 = None
            for f in nexus_files:
                if f['name'] == url_info['filename']:
                    nexus_md5 = f['md5']
            # ignore unit_design.artifact_path update
            # update_unit_design = {}
            # update_unit_design['guid'] = unit_design['data']['guid']
            # update_unit_design[CONF.wecube.wecmdb.artifact_field] = url_info['group']
            # cmdb_client.update(CONF.wecube.wecmdb.citypes.unit_design, [update_unit_design])

            package_rows = [{
                'name': url_info['filename'],
                'deploy_package_url': CONF.wecube.server.rstrip('/') + '/artifacts' + url_info['fullpath'],
                'description': url_info['filename'],
                'md5_value': nexus_md5,
                'upload_user': scoped_globals.GLOBALS.request.auth_user,
                'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'unit_design': unit_design_id
            }]
            package_result = self.create(package_rows)
            return package_result['data']
        else:
            # 从本地Nexus下载并上传到远端Nexus中
            l_nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
            l_artifact_path = self.build_local_nexus_path(unit_design)
            r_nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                               CONF.wecube.nexus.password)
            with r_nexus_client.download_stream(url=download_url) as resp:
                stream = resp.raw
                chunk_size = 1024 * 1024
                with tempfile.TemporaryFile() as tmp_file:
                    chunk = stream.read(chunk_size)
                    while chunk:
                        tmp_file.write(chunk)
                        chunk = stream.read(chunk_size)
                    tmp_file.seek(0)

                    filetype = resp.headers.get('Content-Type', 'application/octet-stream')
                    fileobj = tmp_file
                    filename = download_url.split('/')[-1]
                    upload_result = l_nexus_client.upload(CONF.nexus.repository, l_artifact_path, filename, filetype,
                                                          fileobj)
                    package_rows = [{
                        'name':
                        filename,
                        'deploy_package_url':
                        upload_result['downloadUrl'].replace(CONF.nexus.server.rstrip('/'),
                                                             CONF.wecube.server.rstrip('/') + '/artifacts'),
                        'description':
                        filename,
                        'md5_value':
                        calculate_md5(fileobj),
                        'upload_user':
                        scoped_globals.GLOBALS.request.auth_user,
                        'upload_time':
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'unit_design':
                        unit_design_id
                    }]
                    package_result = self.create(package_rows)
                    return package_result['data']

    def upload_and_create(self, data):
        def _pop_none(d, k):
            if k in d and d[k] is None:
                d.pop(k)

        validates = [
            crud.ColumnValidator('nexusUrl',
                                 validate_on=['update:M'],
                                 rule='1, 255',
                                 rule_type='length',
                                 nullable=False),
            crud.ColumnValidator('baselinePackage',
                                 validate_on=['update:M'],
                                 rule='1, 36',
                                 rule_type='length',
                                 nullable=False),
            crud.ColumnValidator('startFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('stopFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('deployFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('diffConfFile',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('isDecompression',
                                 validate_on=['update:O'],
                                 rule='1, 36',
                                 rule_type='length',
                                 converter=BooleanNomalizedConverter(True),
                                 nullable=True),
            crud.ColumnValidator('dbUpgradeDirectory',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('dbRollbackDirectory',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('dbUpgradeFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('dbRollbackFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
            crud.ColumnValidator('dbDeployFilePath',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
        ]
        clean_data = crud.ColumnValidator.get_clean_data(validates, data, 'update')
        baseline_package_id = clean_data.get('baselinePackage')
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": baseline_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': baseline_package_id})
        baseline_package = resp_json['data']['contents'][0]
        url = CONF.wecube.nexus.server.rstrip(
            '/') + '/repository/' + CONF.wecube.nexus.repository + '/' + clean_data['nexusUrl'].lstrip('/')
        unit_design_id = baseline_package['data']['unit_design']['guid']
        new_pakcage = self.upload_from_nexus(url, unit_design_id)[0]
        # db部署支持, 检查是否用户手动指定值
        b_db_upgrade_detect = True
        b_db_rollback_detect = True
        update_data = {}
        keys = [('startFilePath', 'start_file_path'), ('stopFilePath', 'stop_file_path'),
                ('deployFilePath', 'deploy_file_path'), ('diffConfFile', 'diff_conf_file'),
                ('dbUpgradeDirectory', 'db_upgrade_directory'), ('dbRollbackDirectory', 'db_rollback_directory'),
                ('dbUpgradeFilePath', 'db_upgrade_file_path'), ('dbRollbackFilePath', 'db_rollback_file_path'),
                ('dbDeployFilePath', 'db_deploy_file_path')]
        if 'db_upgrade_directory' not in baseline_package['data']:
            b_db_upgrade_detect = False
        if 'db_rollback_directory' not in baseline_package['data']:
            b_db_upgrade_detect = False
        for s_key, d_key in keys:
            if s_key in clean_data and clean_data[s_key] is not None:
                if d_key == 'db_upgrade_file_path':
                    b_db_upgrade_detect = False
                if d_key == 'db_rollback_file_path':
                    b_db_rollback_detect = False
                update_data[d_key] = self.build_file_object(clean_data[s_key])
            else:
                if d_key in baseline_package['data']:
                    update_data[d_key] = self.build_file_object(baseline_package['data'][d_key])
        update_data['baseline_package'] = baseline_package_id
        update_data['is_decompression'] = baseline_package['data']['is_decompression']
        # db部署支持
        if 'package_type' in baseline_package['data']:
            update_data['package_type'] = baseline_package['data']['package_type']
        self.update(update_data,
                    unit_design_id,
                    new_pakcage['guid'],
                    with_detail=False,
                    db_upgrade_detect=b_db_upgrade_detect,
                    db_rollback_detect=b_db_rollback_detect)
        return {'guid': new_pakcage['guid']}

    def create(self, data):
        cmdb_client = self.get_cmdb_client()
        return cmdb_client.create(CONF.wecube.wecmdb.citypes.deploy_package, data)

    def update(self,
               data,
               unit_design_id,
               deploy_package_id,
               with_detail=True,
               db_upgrade_detect=False,
               db_rollback_detect=False):
        validates = [
            crud.ColumnValidator('guid', validate_on=['update:M'], rule='1, 36', rule_type='length', nullable=False),
            crud.ColumnValidator('baseline_package', validate_on=['update:O'], nullable=True),
            crud.ColumnValidator('deploy_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('start_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('stop_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('diff_conf_file',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('diff_conf_variable',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 nullable=False),
            crud.ColumnValidator('is_decompression',
                                 validate_on=['update:O'],
                                 converter=BooleanNomalizedConverter(True),
                                 nullable=True),
            crud.ColumnValidator('package_type', validate_on=['update:O'], nullable=True),
            crud.ColumnValidator('db_upgrade_directory',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('db_rollback_directory',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('db_upgrade_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('db_rollback_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('db_deploy_file_path',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
        ]
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": deploy_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        data['guid'] = deploy_package_id
        clean_data = crud.ColumnValidator.get_clean_data(validates, data, 'update')
        if 'baseline_package' in clean_data:
            # 兼容旧接口传{}/''/null代表清空的情况
            if isinstance(clean_data['baseline_package'], dict):
                if not clean_data['baseline_package']:
                    clean_data['baseline_package'] = None
                else:
                    clean_data['baseline_package'] = clean_data['baseline_package'].get('guid', None)
            elif isinstance(clean_data['baseline_package'], str) and not clean_data['baseline_package']:
                clean_data['baseline_package'] = None
        # 根据用户指定进行变量绑定
        auto_bind = True
        if 'diff_conf_variable' in data:
            clean_data['diff_conf_variable'] = [c['diffConfigGuid'] for c in data['diff_conf_variable'] if c['bound']]
            auto_bind = False
        # 根据diff_conf_file计算变量进行更新绑定
        if 'diff_conf_file' in data:
            new_diff_conf_file_list = set([f['filename'] for f in data['diff_conf_file']])
            old_diff_conf_file_list = set(
                [f['filename'] for f in self.build_file_object(deploy_package['data']['diff_conf_file'])])
            # diff_conf_file值并未发生改变，无需下载文件更新变量
            if new_diff_conf_file_list != old_diff_conf_file_list:
                package_cached_dir = self.ensure_package_cached(deploy_package['data']['guid'],
                                                                deploy_package['data']['deploy_package_url'])
                self.update_file_variable(package_cached_dir, data['diff_conf_file'])
                # 获取所有差异化配置项
                empty_query = {"filters": [], "paging": False}
                resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, empty_query)
                all_diff_configs = resp_json['data']['contents']
                finder = artifact_utils.CaseInsensitiveDict()
                for conf in all_diff_configs:
                    finder[conf['data']['variable_name']] = conf
                package_diff_configs = []
                new_diff_configs = set()
                exist_diff_configs = set()
                for conf_file in data['diff_conf_file']:
                    package_diff_configs.extend(conf_file['configKeyInfos'])
                for diff_conf in package_diff_configs:
                    if diff_conf['key'] not in finder:
                        new_diff_configs.add(diff_conf['key'])
                    else:
                        exist_diff_configs.add(finder[diff_conf['key']]['data']['guid'])
                # 创建新的差异化变量项
                bind_variables = list(exist_diff_configs)
                if len(new_diff_configs):
                    resp_json = cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [{
                        'variable_name': c,
                        'description': c
                    } for c in new_diff_configs])
                    bind_variables.extend([c['guid'] for c in resp_json['data']])
                if auto_bind:
                    clean_data['diff_conf_variable'] = bind_variables
        if db_upgrade_detect:
            clean_data['db_upgrade_file_path'] = FileNameConcater().convert(
                self.find_files_by_status(clean_data['baseline_package'], deploy_package_id,
                                          clean_data['db_upgrade_directory'].split('|'), ['new', 'changed']))
        if db_rollback_detect:
            clean_data['db_rollback_file_path'] = FileNameConcater().convert(
                self.find_files_by_status(clean_data['baseline_package'], deploy_package_id,
                                          clean_data['db_rollback_directory'].split('|'), ['new', 'changed']))
        resp_json = cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, [clean_data])
        if with_detail:
            return self.get(unit_design_id, deploy_package_id)
        return resp_json['data']

    def find_files_by_status(self, baseline_id, package_id, source_dirs, status):
        results = []
        files = self.filetree(None, package_id, baseline_id, False, source_dirs)
        for f in files:
            if f['exists'] and not f['isDir'] and f['comparisonResult'] in status:
                # convert data field
                f['filename'] = f.pop('path', None)
                f.pop('name', None)
                results.append(f)
        return results

    def get(self, unit_design_id, deploy_package_id):
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": deploy_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = (deploy_package['data'].get('baseline_package', None) or {})
        empty_query = {"filters": [], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, empty_query)
        all_diff_configs = resp_json['data']['contents']
        result = {}
        result['packageId'] = deploy_package_id
        result['baseline_package'] = baseline_package.get('guid', None)

        result['is_decompression'] = utils.bool_from_string(deploy_package['data']['is_decompression'], default=True)
        # |切割为列表
        result['deploy_file_path'] = self.build_file_object(deploy_package['data']['deploy_file_path'])
        result['start_file_path'] = self.build_file_object(deploy_package['data']['start_file_path'])
        result['stop_file_path'] = self.build_file_object(deploy_package['data']['stop_file_path'])
        result['diff_conf_file'] = self.build_file_object(deploy_package['data']['diff_conf_file'])
        result['diff_conf_variable'] = deploy_package['data']['diff_conf_variable']
        # 文件对比[same, changed, new, deleted]
        baseline_cached_dir = None
        package_cached_dir = None
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                             baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['data']['guid'],
                                                        deploy_package['data']['deploy_package_url'])
        # 更新文件的md5,comparisonResult,isDir
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['deploy_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['start_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['stop_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['diff_conf_file'])
        # 更新差异化配置文件的变量列表
        self.update_file_variable(package_cached_dir, result['diff_conf_file'])
        package_diff_configs = []
        for conf_file in result['diff_conf_file']:
            package_diff_configs.extend(conf_file['configKeyInfos'])
        # 更新差异化变量bound/diffConfigGuid/diffExpr/fixedDate/key/type
        result['diff_conf_variable'] = self.update_diff_conf_variable(all_diff_configs, package_diff_configs,
                                                                      result['diff_conf_variable'])
        # db部署支持
        if 'package_type' in deploy_package['data']:
            result['package_type'] = deploy_package['data']['package_type']

        fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                  'db_deploy_file_path')
        for field in fields:
            if field in deploy_package['data']:
                result[field] = self.build_file_object(deploy_package['data'][field])
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        return result

    def baseline_compare(self, unit_design_id, deploy_package_id, baseline_package_id):
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": deploy_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        query = {"filters": [{"name": "guid", "operator": "eq", "value": baseline_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': baseline_package_id})
        baseline_package = resp_json['data']['contents'][0]

        result = {}
        # |切割为列表
        result['deploy_file_path'] = self.build_file_object(baseline_package['data']['deploy_file_path'])
        result['start_file_path'] = self.build_file_object(baseline_package['data']['start_file_path'])
        result['stop_file_path'] = self.build_file_object(baseline_package['data']['stop_file_path'])
        result['diff_conf_file'] = self.build_file_object(baseline_package['data']['diff_conf_file'])
        # DB部署支持
        fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                  'db_deploy_file_path')
        for field in fields:
            if field in baseline_package['data']:
                result[field] = self.build_file_object(baseline_package['data'][field])

        # 文件对比[same, changed, new, deleted]
        baseline_cached_dir = None
        package_cached_dir = None
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        baseline_cached_dir = self.ensure_package_cached(baseline_package['data']['guid'],
                                                         baseline_package['data']['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['data']['guid'],
                                                        deploy_package['data']['deploy_package_url'])
        # 更新文件的md5,comparisonResult,isDir
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['deploy_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['start_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['stop_file_path'])
        self.update_file_status(baseline_cached_dir, package_cached_dir, result['diff_conf_file'])
        # DB部署支持
        if 'db_upgrade_directory' in result:
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_upgrade_directory'])
            result['db_upgrade_file_path'] = self.find_files_by_status(
                baseline_package_id, deploy_package_id, [i['filename'] for i in result['db_upgrade_directory']],
                ['new', 'changed'])
        if 'db_rollback_directory' in result:
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_rollback_directory'])
            result['db_rollback_file_path'] = self.find_files_by_status(
                baseline_package_id, deploy_package_id, [i['filename'] for i in result['db_rollback_directory']],
                ['new', 'changed'])
        if 'db_deploy_file_path' in result:
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_deploy_file_path'])
        return result

    def baseline_files_compare(self, data, unit_design_id, deploy_package_id, baseline_package_id):
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": deploy_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = None
        if baseline_package_id:
            query = {"filters": [{"name": "guid", "operator": "eq", "value": baseline_package_id}], "paging": False}
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                               {'rid': baseline_package_id})
            baseline_package = resp_json['data']['contents'][0]
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        baseline_cached_dir = None
        package_cached_dir = None
        package_cached_dir = self.ensure_package_cached(deploy_package['data']['guid'],
                                                        deploy_package['data']['deploy_package_url'])
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['data']['guid'],
                                                             baseline_package['data']['deploy_package_url'])
        results = []
        max_length = data.get('content_length', None) or -1
        for f in data['files']:
            package_filepath = os.path.join(package_cached_dir, f['path'])
            exists = os.path.exists(package_filepath)
            is_dir = os.path.isdir(package_filepath)
            b_package_filepath = None
            b_exists = None
            b_is_dir = None
            if baseline_package:
                b_package_filepath = os.path.join(baseline_cached_dir, f['path'])
                b_exists = os.path.exists(b_package_filepath)
                b_is_dir = os.path.isdir(b_package_filepath)
            if exists is False and (b_exists is False or (not baseline_package and not b_exists)):
                raise exceptions.PluginError(message=_('%(file)s not exists in both package & baseline package') %
                                             {'file': f['path']})
            if is_dir is True or b_is_dir is True:
                raise exceptions.PluginError(message=_('%(file)s is dir, not regular file') % {'file': f['path']})
            result = {'path': f['path'], 'content': '', 'baseline_content': ''}
            if not is_dir and exists:
                with open(package_filepath, errors='replace') as f:
                    result['content'] = f.read(max_length)
            if not b_is_dir and b_exists:
                with open(b_package_filepath, errors='replace') as f:
                    result['baseline_content'] = f.read(max_length)
            results.append(result)
        return results

    def update_tree_status(self, baseline_path, package_path, nodes):
        self.update_file_status(baseline_path, package_path, nodes, file_key='name')
        for n in nodes:
            subpath = n['name']
            if n['children'] and n['isDir']:
                self.update_tree_status(None if not baseline_path else os.path.join(baseline_path, subpath),
                                        os.path.join(package_path, subpath), n['children'])

    def filetree(self, unit_design_id, deploy_package_id, baseline_package_id, expand_all, files):
        def _scan_dir(basepath, subpath):
            results = []
            path = os.path.join(basepath, subpath)
            if os.path.exists(path):
                for e in os.scandir(path):
                    results.append({
                        'children': [],
                        'comparisonResult': None,
                        'exists': None,
                        'isDir': e.is_dir(),
                        'md5': None,
                        'name': e.name,
                        'path': e.path[len(basepath) + 1:],
                    })
            return results

        def _add_children_node(filename, subpath, file_list, is_dir=False):
            node = None
            if filename not in [i['name'] for i in file_list]:
                node = {
                    'children': [],
                    'comparisonResult': None,
                    'exists': None,
                    'isDir': None,
                    'md5': None,
                    'name': filename,
                    'path': os.path.join(subpath, filename),
                }
                file_list.append(node)
            else:
                for i in file_list:
                    if filename == i['name']:
                        node = i
            node['isDir'] = is_dir
            return node

        def _generate_tree_from_list(basepath, file_list):
            expanded_dirs = set()
            root_nodes = []
            if not file_list:
                root_nodes.extend(_scan_dir(basepath, ''))
            else:
                for f in file_list:
                    new_f = f.lstrip('/')
                    parts = new_f.split('/')
                    # filename on root
                    if len(parts) == 1:
                        subpath = ''
                        scan_results = []
                        if (basepath, subpath) not in expanded_dirs:
                            scan_results = _scan_dir(basepath, subpath)
                            expanded_dirs.add((basepath, subpath))
                        root_nodes.extend(scan_results)
                        if len(parts[0]) > 0:
                            _add_children_node(parts[0], subpath, root_nodes)
                    # ends with a/b/c/
                    else:
                        filename = parts.pop(-1)
                        path_nodes = root_nodes
                        subpath = ''
                        for idx in range(len(parts)):
                            # sec protection: you can not list dir out of basepath
                            if parts[idx] not in ('', '.', '..'):
                                scan_results = []
                                if (basepath, subpath) not in expanded_dirs:
                                    scan_results = _scan_dir(basepath, subpath)
                                    expanded_dirs.add((basepath, subpath))
                                path_nodes.extend(scan_results)
                                node = _add_children_node(parts[idx], subpath, path_nodes, True)
                                path_nodes = node['children']
                                subpath = os.path.join(subpath, parts[idx])
                        scan_results = []
                        if (basepath, subpath) not in expanded_dirs:
                            scan_results = _scan_dir(basepath, subpath)
                            expanded_dirs.add((basepath, subpath))
                        path_nodes.extend(scan_results)
                        if filename:
                            _add_children_node(filename, subpath, path_nodes)
            return root_nodes

        def _get_file_list(baseline_path, package_path, file_list):
            results = []
            for f in file_list:
                new_f = f.lstrip('/')
                parts = new_f.split('/')
                subpath = os.path.join(*[p for p in parts if p not in ('', '.', '..')])
                new_file_list = _scan_dir(package_path, subpath)
                self.update_file_status(None if not baseline_path else os.path.join(baseline_path, subpath),
                                        os.path.join(package_path, subpath),
                                        new_file_list,
                                        file_key='name')
                results.extend(new_file_list)
            return results

        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": deploy_package_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = None
        if baseline_package_id:
            query = {"filters": [{"name": "guid", "operator": "eq", "value": baseline_package_id}], "paging": False}
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                               {'rid': baseline_package_id})
            baseline_package = resp_json['data']['contents'][0]
        baseline_cached_dir = None
        package_cached_dir = None
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['data']['guid'],
                                                             baseline_package['data']['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['data']['guid'],
                                                        deploy_package['data']['deploy_package_url'])
        results = []
        if expand_all:
            results = _generate_tree_from_list(package_cached_dir, files)
            self.update_tree_status(baseline_cached_dir, package_cached_dir, results)
        else:
            results = _get_file_list(baseline_cached_dir, package_cached_dir, files)
        return results

    def update_file_status(self, baseline_cached_dir, package_cached_dir, files, file_key='filename'):
        '''
        更新文件内容：存在性，md5，文件/目录
        '''
        for i in files:
            b_filepath = os.path.join(baseline_cached_dir, i[file_key]) if baseline_cached_dir else None
            filepath = os.path.join(package_cached_dir, i[file_key])
            b_exists = os.path.exists(b_filepath) if baseline_cached_dir else None
            exists = os.path.exists(filepath)
            b_md5 = None
            md5 = None
            if b_exists:
                i['isDir'] = os.path.isdir(b_filepath)
                if not i['isDir']:
                    b_md5 = calculate_file_md5(b_filepath)
            if exists:
                i['isDir'] = os.path.isdir(filepath)
                if not i['isDir']:
                    md5 = calculate_file_md5(filepath)
            i['exists'] = exists
            i['md5'] = md5
            # check only baseline_cached_dir is valid
            if baseline_cached_dir:
                # file type
                if not i['isDir']:
                    # same
                    if exists and b_exists and b_md5 == md5:
                        i['comparisonResult'] = 'same'
                    # changed
                    elif exists and b_exists and b_md5 != md5:
                        i['comparisonResult'] = 'changed'
                    # new
                    elif exists and not b_exists:
                        i['comparisonResult'] = 'new'
                    # deleted
                    elif not exists and b_exists:
                        i['comparisonResult'] = 'deleted'
                    else:
                        i['comparisonResult'] = 'deleted'
                else:
                    # dir type
                    # same
                    if exists and b_exists:
                        i['comparisonResult'] = 'same'
                    # new
                    elif exists and not b_exists:
                        i['comparisonResult'] = 'new'
                    # deleted
                    elif not exists and b_exists:
                        i['comparisonResult'] = 'deleted'
                    else:
                        i['comparisonResult'] = 'deleted'
            # fix all not exist to deleted
            if not exists:
                i['comparisonResult'] = 'deleted'
        return files

    def update_file_variable(self, package_cached_dir, files):
        '''
        解析文件差异化变量
        '''
        spliters = [s.strip() for s in CONF.encrypt_variable_prefix.split(',')]
        spliters.extend([s.strip() for s in CONF.file_variable_prefix.split(',')])
        spliters.extend([s.strip() for s in CONF.default_special_replace.split(',')])
        for i in files:
            filepath = os.path.join(package_cached_dir, i['filename'])
            if os.path.exists(filepath):
                with open(filepath, errors='replace') as f:
                    content = f.read()
                    i['configKeyInfos'] = artifact_utils.variable_parse(content, spliters)
            else:
                i['configKeyInfos'] = []

    def update_diff_conf_variable(self, all_diff_configs, package_diff_configs, bounded_diff_configs):
        '''
        更新差异化变量绑定内容
        package_diff_configs 是所有差异化变量文件的解析结果列表，元素可以重复
        bounded_diff_configs 是物料包CI中差异化变量字段值（列表）
        '''
        results = []
        finder = artifact_utils.CaseInsensitiveDict()
        p_finder = artifact_utils.CaseInsensitiveDict()
        b_finder = artifact_utils.CaseInsensitiveDict()
        for conf in all_diff_configs:
            finder[conf['data']['variable_name']] = conf
        for pconf in package_diff_configs:
            p_finder[pconf['key']] = pconf
        for bconf in bounded_diff_configs:
            b_finder[bconf['variable_name']] = bconf
        for k, v in p_finder.items():
            conf = finder.get(k, None)
            p_conf = p_finder.get(k, None)
            results.append({
                'bound': k in b_finder,
                'diffConfigGuid': None if conf is None else conf['data']['guid'],
                'diffExpr': None if conf is None else conf['data']['variable_value'],
                'fixedDate': None if conf is None else conf['data']['fixed_date'],
                'key': k if conf is None else conf['data']['variable_name'],
                'type': None if p_conf is None else p_conf['type']
            })
        return results

    def ensure_package_cached(self, guid, url):
        cache_dir = CONF.pakcage_cache_dir
        file_cache_dir = os.path.join(cache_dir, guid)
        with artifact_utils.lock(hashlib.sha1(file_cache_dir.encode()).hexdigest(), timeout=300) as locked:
            if locked:
                if os.path.exists(file_cache_dir):
                    LOG.info('using cache: %s for package: %s', file_cache_dir, guid)
                else:
                    with tempfile.TemporaryDirectory() as download_path:
                        LOG.info('download from: %s for pakcage: %s', url, guid)
                        filepath = self.download_from_url(download_path, url)
                        LOG.info('download complete')
                        LOG.info('unpack package: %s to %s', guid, file_cache_dir)
                        try:
                            # FIXME: exception for some files
                            artifact_utils.unpack_file(filepath, file_cache_dir)
                        except Exception as e:
                            shutil.rmtree(file_cache_dir, ignore_errors=True)
                            LOG.error('unpack failed')
                            if str(e).find('bad subsequent header') >= 0:
                                raise exceptions.PluginError(message=_(
                                    'unpack file error: %(detail)s, is file contains paxheader(mac archive) and modify with 7zip? (cause paxheader corruption)'
                                    % {'detail': str(e)}))
                            raise exceptions.PluginError(message=_('unpack file error: %(detail)s' %
                                                                   {'detail': str(e)}))
                        LOG.info('unpack complete')
            else:
                raise OSError(_('failed to acquire lock, package cache may not be available'))
        return file_cache_dir

    def download_from_url(self, dir_path, url, random_name=False):
        filename = url.rsplit('/', 1)[-1]
        if random_name:
            filename = '%s_%s' % (utils.generate_uuid(), filename)
        filepath = os.path.join(dir_path, filename)
        if url.startswith(CONF.wecube.server):
            # nexus url
            nexus_server = None
            nexus_username = None
            nexus_password = None
            if utils.bool_from_string(CONF.use_remote_nexus_only):
                nexus_server = CONF.wecube.nexus.server.rstrip('/')
                nexus_username = CONF.wecube.nexus.username
                nexus_password = CONF.wecube.nexus.password
            else:
                nexus_server = CONF.nexus.server.rstrip('/')
                nexus_username = CONF.nexus.username
                nexus_password = CONF.nexus.password
            # 替换外部下载地址为Nexus内部地址
            new_url = url.replace(CONF.wecube.server.rstrip('/') + '/artifacts', nexus_server)
            client = nexus.NeuxsClient(nexus_server, nexus_username, nexus_password)
            client.download_file(filepath, url=new_url)
        else:
            client = s3.S3Downloader(url)
            client.download_file(filepath, CONF.wecube.s3.access_key, CONF.wecube.s3.secret_key)
        return filepath


class UnitDesignNexusPackages(WeCubeResource):
    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design['data'].get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def list_by_post(self, query, unit_design_id):
        if not is_upload_nexus_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        cmdb_client = self.get_cmdb_client()
        query = {"filters": [{"name": "guid", "operator": "eq", "value": unit_design_id}], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                         CONF.wecube.nexus.password)
        return nexus_client.list(CONF.wecube.nexus.repository,
                                 self.get_unit_design_artifact_path(unit_design),
                                 extensions=['.zip', '.tar', '.tar.gz', 'tgz', '.jar'])


class DiffConfig(WeCubeResource):
    def update(self, data):
        cmdb_client = self.get_cmdb_client()
        format_datas = []
        for d in data:
            format_datas.append({'guid': d['id'], 'variable_value': d['variable_value']})
        resp_json = cmdb_client.update(CONF.wecube.wecmdb.citypes.diff_config, format_datas)
        return resp_json['data']

    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        query = {"dialect": {"showCiHistory": False}, "filters": [], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
        return [i['data'] for i in resp_json['data']['contents']]