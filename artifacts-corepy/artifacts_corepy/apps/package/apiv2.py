# coding=utf-8

from __future__ import absolute_import

import datetime
import hashlib
import fnmatch
import os
import logging
import collections
import re
import shutil
import tempfile
import json
import tarfile
import os.path
import urllib.parse
from collections import namedtuple
from talos.core import config
from talos.core import utils
from talos.db import crud
from talos.db import converter
from talos.db import validator
from talos.core.i18n import _
from talos.utils import scoped_globals

from artifacts_corepy.common import exceptions
from artifacts_corepy.common import nexus
from artifacts_corepy.common import s3
from artifacts_corepy.common import wecmdbv2 as wecmdb
from artifacts_corepy.common import utils as artifact_utils
from artifacts_corepy.common import constant

LOG = logging.getLogger(__name__)
CONF = config.CONF

# Common
field_pkg_baseline_package_name = 'baseline_package'
field_pkg_is_decompression_name = 'is_decompression' # true,false as string
field_pkg_package_type_name = 'package_type' # APP DB APP&DB
field_pkg_key_service_code_name = 'key_service_code'
fields_pkg_common = [field_pkg_baseline_package_name, field_pkg_is_decompression_name, field_pkg_package_type_name, 
                     field_pkg_key_service_code_name]
field_pkg_baseline_package_default_value = None
field_pkg_is_decompression_default_value = 'true'
field_pkg_package_type_default_value = constant.PackageType.default
field_pkg_key_service_code_default_value = []
# APP
field_pkg_diff_conf_directory_name = 'diff_conf_directory'
field_pkg_diff_conf_file_name = 'diff_conf_file'
field_pkg_script_file_directory_name = 'script_file_directory'
field_pkg_deploy_file_path_name = 'deploy_file_path'
field_pkg_start_file_path_name = 'start_file_path'
field_pkg_stop_file_path_name = 'stop_file_path'
field_pkg_log_file_directory_name = 'log_file_directory'
field_pkg_log_file_trade_name = 'log_file_trade'
field_pkg_log_file_keyword_name = 'log_file_keyword'
field_pkg_log_file_metric_name = 'log_file_metric'
field_pkg_log_file_trace_name = 'log_file_trace'
fields_pkg_app = [field_pkg_diff_conf_directory_name, field_pkg_diff_conf_file_name, field_pkg_script_file_directory_name, 
                  field_pkg_deploy_file_path_name, field_pkg_start_file_path_name, field_pkg_stop_file_path_name,
                  field_pkg_log_file_directory_name, field_pkg_log_file_trade_name, field_pkg_log_file_keyword_name,
                  field_pkg_log_file_metric_name, field_pkg_log_file_trace_name]
field_pkg_diff_conf_directory_default_value = 'conf'
field_pkg_diff_conf_file_default_value = ''
field_pkg_script_file_directory_default_value = 'bin'
field_pkg_deploy_file_path_default_value = 'bin/deploy.sh'
field_pkg_start_file_path_default_value = 'bin/start.sh'
field_pkg_stop_file_path_default_value = 'bin/stop.sh'
field_pkg_log_file_directory_default_value = 'logs'
field_pkg_log_file_trade_default_value = 'logs/trade.log'
field_pkg_log_file_keyword_default_value = 'logs/keyword.log'
field_pkg_log_file_metric_default_value = 'logs/metric.log'
field_pkg_log_file_trace_default_value = 'logs/trace.log'

# DB
field_pkg_db_deploy_file_directory_name = 'db_deploy_file_directory'
field_pkg_db_deploy_file_path_name = 'db_deploy_file_path'
field_pkg_db_diff_conf_directory_name = 'db_diff_conf_directory'
field_pkg_db_diff_conf_file_name = 'db_diff_conf_file'
field_pkg_db_rollback_directory_name = 'db_rollback_directory'
field_pkg_db_rollback_file_path_name = 'db_rollback_file_path'
field_pkg_db_upgrade_directory_name = 'db_upgrade_directory'
field_pkg_db_upgrade_file_path_name = 'db_upgrade_file_path'
fields_pkg_db = [field_pkg_db_deploy_file_directory_name, field_pkg_db_deploy_file_path_name, field_pkg_db_diff_conf_directory_name, 
                  field_pkg_db_diff_conf_file_name, field_pkg_db_rollback_directory_name, field_pkg_db_rollback_file_path_name,
                  field_pkg_db_upgrade_directory_name, field_pkg_db_upgrade_file_path_name]
fields_pkg_all = []
fields_pkg_all.extend(fields_pkg_common)
fields_pkg_all.extend(fields_pkg_app)
fields_pkg_all.extend(fields_pkg_db)
field_pkg_db_deploy_file_directory_default_value = 'db/install'
field_pkg_db_diff_conf_directory_default_value = 'db'
field_pkg_db_diff_conf_file_default_value = ''
field_pkg_db_rollback_directory_default_value = 'db/rollback'
field_pkg_db_rollback_file_path_default_value = ''
field_pkg_db_upgrade_directory_default_value = 'db/update'
field_pkg_db_upgrade_file_path_default_value = ''

# var
field_pkg_diff_conf_var_name = 'diff_conf_variable'
field_pkg_db_diff_conf_var_name = 'db_diff_conf_variable'

field_pkg_overwrite_map_str = os.getenv('ARTIFACTS_DEPLOY_PACKAGE_FIELD_MAP', default='')
field_pkg_overwrite_map = {}
if field_pkg_overwrite_map_str.strip():
    try:
        field_pkg_overwrite_map = json.loads(field_pkg_overwrite_map_str)
    except Exception as e:
        LOG.error('Failed to parse ARTIFACTS_DEPLOY_PACKAGE_FIELD_MAP: %s', field_pkg_overwrite_map_str)
        LOG.exception(e)
    local_vars = locals()
    for k, v in field_pkg_overwrite_map.items():
        if k.startswith('field_pkg_') and (k.endswith('_name') or k.endswith('_default_value')) and k in local_vars:
            local_vars[k] = v

field_diff_conf_tpl_map_str = os.getenv('ARTIFACTS_DIFF_CONF_TEMPLATE_MAP', default='')
field_diff_conf_tpl_map = {}
if field_diff_conf_tpl_map_str.strip():
    try:
        field_diff_conf_tpl_map = json.loads(field_diff_conf_tpl_map_str)
    except Exception as e:
        LOG.error('Failed to parse ARTIFACTS_DIFF_CONF_TEMPLATE_MAP: %s', field_diff_conf_tpl_map_str)
        LOG.exception(e)  

def is_upload_local_enabled():
    return utils.bool_from_string(CONF.wecube.upload_enabled)


def is_upload_nexus_enabled():
    return utils.bool_from_string(CONF.wecube.upload_nexus_enabled)

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def calculate_md5(fileobj):
    hasher = hashlib.md5()
    chunk_size = 64 * 1024
    fileobj.seek(0)
    chunk = fileobj.read(chunk_size)
    while chunk:
        hasher.update(chunk)
        chunk = fileobj.read(chunk_size)
    return hasher.hexdigest()


def calculate_file_md5(filepath):
    with open(filepath, 'rb') as fileobj:
        return calculate_md5(fileobj)

def split_to_list(value, spliter=None):
    if spliter is None:
        spliter = r'[|,]'
    return re.split(spliter, value)

class FileNameConcater(converter.NullConverter):
    def convert(self, value):
        return ','.join([i.get('filename') for i in value if i.get('filename')])

class FilePathConcater(converter.NullConverter):
    def convert(self, value):
        return ','.join([i.get('path') for i in value if i.get('path')])
    
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

    def list_by_post(self, query):
        pass


class ProcessDef(WeCubeResource):
    def list(self, params):
        params['plugin'] = 'artifacts'
        params['permission'] = 'USE'
        if 'all' not in params:
            params['all'] = 'N'
        if 'rootEntity' not in params:
            params['rootEntity'] = 'wecmdb:' + CONF.wecube.wecmdb.citypes.deploy_package
        if 'rootEntityGuid' not in params:
            params['rootEntityGuid'] = params['rootEntityGuid']
        api_client = self.get_cmdb_client()
        url = self.server + '/platform/v1/public/process/definitions'
        return api_client.get(url, params, check_resp=False)

class SystemDesign(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "all"
            },
            "filters": [{
                "name": "confirm_time",
                "operator": "notNull",
                "value": None
            }, {
                "name": "confirm_time",
                "operator": "ne",
                "value": ""
            }],
            "paging":
            False,
            "sorting": {
                "asc": False,
                "field": "confirm_time"
            }
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.system_design, query)
        last_version = collections.OrderedDict()
        for content in resp_json['data']['contents']:
            r_guid = content['guid']
            if r_guid not in last_version:
                last_version[r_guid] = content
        return {
            'contents': list(last_version.values()),
            'pageInfo': None,
        }

    def get(self, rid):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "all"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": rid
            }],
            "paging": False,
            "sorting": {
                "asc": False,
                "field": "confirm_time"
            }
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.system_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") % {'rid': rid})
        confirm_time = ''
        for content in resp_json['data']['contents']:
            if content['confirm_time']:
                confirm_time = content['confirm_time']
                break
        results = []
        if confirm_time:
            resp_json = cmdb_client.view_data(CONF.wecube.wecmdb.system_design_view, rid, confirm_time)
            results = resp_json['data']
        return results


class SpecialConnector(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        return cmdb_client.special_connector()


class CiTypes(WeCubeResource):
    def list(self, params):
        cmdb_client = self.get_cmdb_client()
        with_attributes = params.get('with-attributes', 'no')
        status = params.get('status', 'created,dirty')
        if isinstance(status, list):
            status = ','.join(status)
        query = {"with-attributes": with_attributes, "status": status, "attr-type-status": status}
        resp_json = cmdb_client.citypes(query)
        return resp_json['data']

    def get_references(self, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.citype_refs(ci_type_id)
        return [item for item in resp_json['data'] if item['inputType'] in ["ref", "multiRef"]]

    def get_attributes(self, accept_types, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.citype_attrs(ci_type_id)
        attrs = resp_json['data']
        attrs.sort(key=lambda x: x['uiFormOrder'])
        return attrs

    def update_state(self, data, operation):
        cmdb_client = self.get_cmdb_client()
        citype = data[0]['ciTypeId']
        new_data = []
        for item in data:
            del item['ciTypeId']
            new_data.append(item)
        result = cmdb_client.state_operation(operation, citype, new_data)
        return result['data']

    def batch_delete(self, data, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        data = [{'guid': item} for item in data]
        result = cmdb_client.delete(ci_type_id, data)
        return result['data']


class EnumCodes(WeCubeResource):
    def get(self, cat_id):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.enumcodes(cat_id)
        return resp_json['data']


class CITypeOperations(WeCubeResource):
    def get(self, ci_type_id):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.ci_operations(ci_type_id)
        return resp_json['data']


class PackageHistory(WeCubeResource):
    def get(self, deploy_package_id):
        cmdb_client = self.get_cmdb_client()
        resp_json = cmdb_client.history(deploy_package_id)
        return resp_json['data']


class UnitDesignPackages(WeCubeResource):
    def set_package_query_fields(self, query):
        # query.setdefault('resultColumns', [
        #     "baseline_package", "code", "deploy_package_url", "db_upgrade_file_path", "db_rollback_file_path",
        #     "description", "package_type", "stop_file_path", "start_file_path", "state", "fixed_date", "unit_design",
        #     "is_decompression", "db_deploy_file_path", "created_by", "db_rollback_directory", "key_name",
        #     "db_upgrade_directory", "upload_time", "upload_user", "deploy_file_path", "diff_conf_file",
        #     "db_diff_conf_file", "name", "updated_by", "guid", "created_date", "updated_date", "md5_value", "state_code"
        # ])
        pass

    def list_by_post(self, query, unit_design_id):
        cmdb_client = self.get_cmdb_client()
        query.setdefault('dialect', {"queryMode": "new"})
        query.setdefault('filters', [])
        query.setdefault('paging', False)
        self.set_package_query_fields(query)
        query['filters'].append({"name": "unit_design", "operator": "eq", "value": unit_design_id})
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        for i in resp_json['data']['contents']:
            i[field_pkg_package_type_name] = i.get(field_pkg_package_type_name, constant.PackageType.default) or constant.PackageType.default
            i[field_pkg_is_decompression_name] = i.get(field_pkg_is_decompression_name, field_pkg_is_decompression_default_value) or field_pkg_is_decompression_default_value
            i[field_pkg_key_service_code_name] = i.get(field_pkg_key_service_code_name, field_pkg_key_service_code_default_value) or field_pkg_key_service_code_default_value
            fields = (field_pkg_diff_conf_directory_name, field_pkg_diff_conf_file_name,
                  field_pkg_script_file_directory_name, field_pkg_deploy_file_path_name, 
                  field_pkg_start_file_path_name, field_pkg_stop_file_path_name,
                  field_pkg_log_file_directory_name,field_pkg_log_file_trade_name, 
                  field_pkg_log_file_keyword_name, field_pkg_log_file_metric_name, field_pkg_log_file_trace_name,)
            for field in fields:
                i[field] = self.build_file_object(i.get(field, None))
            # db部署支持
            fields = (field_pkg_db_deploy_file_directory_name, field_pkg_db_deploy_file_path_name,
                  field_pkg_db_diff_conf_directory_name, field_pkg_db_diff_conf_file_name,
                  field_pkg_db_upgrade_directory_name, field_pkg_db_rollback_file_path_name, 
                  field_pkg_db_rollback_directory_name, field_pkg_db_upgrade_file_path_name,)
            for field in fields:
                i[field] = self.build_file_object(i.get(field, None))
        return resp_json['data']

    def build_file_object(self, filenames, spliter=None):
        if spliter is None:
            spliter = r'[|,]' 
        if not filenames:
            return []
        return [{
            'comparisonResult': None,
            'configKeyInfos': [],
            'filename': f,
            'isDir': None,
            'md5': None
        } for f in re.split(spliter, filenames)]

    def build_local_nexus_path(self, unit_design):
        return unit_design['key_name']

    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design.get(CONF.wecube.wecmdb.artifact_field, None)
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
        if ''.count('/') >= 1:
            ret['group'] = '/' + results[1].rsplit('/', 1)[0]
        else:
            ret['group'] = '/'
        return ret
    
    def _is_compose_package(self, filename:str) -> bool:
        if filename.startswith('[W]') and '_weart' in filename:
            return True
        return False
    
    def _conv_diff_conf_type(self, diff_conf_type:str) -> str:
        """
        将差异化配置文件类型转换为对应的枚举类型
        """
        variable_prefix_encrypt = [] if not CONF.encrypt_variable_prefix.strip() else [s.strip() for s in CONF.encrypt_variable_prefix.split(',')]
        variable_prefix_file = [] if not CONF.file_variable_prefix.strip() else [s.strip() for s in CONF.file_variable_prefix.split(',')]
        variable_prefix_default = [] if not CONF.default_special_replace.strip() else [s.strip() for s in CONF.default_special_replace.split(',')]
        variable_prefix_global = [] if not CONF.global_variable_prefix.strip() else [s.strip() for s in CONF.global_variable_prefix.split(',')]
        if diff_conf_type in variable_prefix_encrypt:
            return 'ENCRYPTED'
        elif diff_conf_type in variable_prefix_file:
            return 'FILE'
        elif diff_conf_type in variable_prefix_default:
            return 'PRIVATE'
        elif diff_conf_type in variable_prefix_global:
            return 'GLOBAL'
        return ''
    
    """上传组合物料包[含差异化变量，包配置，包文件]
    """    
    def upload_compose_package(self, compose_filename:str, compose_fileobj, unit_design_id:str, force_operator=None, baseline_package=None):
        # 组合包上传需要解压并且提取真正包上传到nexus中
        chunk_size = 1024 * 1024
        with tempfile.NamedTemporaryFile('w+b',suffix='.tar.gz') as upload_stream_file:
            chunk = compose_fileobj.read(chunk_size)
            while chunk:
                upload_stream_file.write(chunk)
                chunk = compose_fileobj.read(chunk_size)
            upload_stream_file.flush()
            deploy_package = None
            pacakge_app_diffconfigs = None
            pacakge_db_diffconfigs = None
            new_download_url = ''
            with tempfile.TemporaryDirectory() as file_cache_dir:
                # 解压组合包
                LOG.info('unpack package: %s to %s', compose_filename, file_cache_dir)
                try:
                    artifact_utils.unpack_file(upload_stream_file.name, file_cache_dir)
                except Exception as e:
                    LOG.error('unpack failed')
                    if str(e).find('bad subsequent header') >= 0:
                        raise exceptions.PluginError(message=_(
                            'unpack file error: %(detail)s, is file contains paxheader(mac archive) and modify with 7zip? (cause paxheader corruption)'
                            % {'detail': str(e)}))
                    raise exceptions.PluginError(message=_('unpack file error: %(detail)s' %
                                                            {'detail': str(e)}))
                LOG.info('unpack complete')
                
                filenames = os.listdir(file_cache_dir)
                # 提取包配置
                filename = 'package.json'
                if filename in filenames:
                    filenames.remove(filename)
                    with open(os.path.join(file_cache_dir, filename), 'r') as f:
                        deploy_package = json.loads(f.read())
                # 提取app差异化变量
                filename = 'package_app_diffconfigs.json'
                if filename in filenames:
                    filenames.remove(filename)
                    with open(os.path.join(file_cache_dir, filename), 'r') as f:
                        pacakge_app_diffconfigs = json.loads(f.read())
                # 提取db差异化变量
                filename = 'package_db_diffconfigs.json'
                if filename in filenames:
                    filenames.remove(filename)
                    with open(os.path.join(file_cache_dir, filename), 'r') as f:
                        pacakge_db_diffconfigs = json.loads(f.read())
                # 剩下的即是原始物料包
                if len(filenames) ==1:
                    filename = filenames[0]
                    filename = os.path.join(file_cache_dir, filename)
                    unit_design = self._get_unit_design_by_id(unit_design_id)
                    nexus_server = None
                    if utils.bool_from_string(CONF.use_remote_nexus_only):
                        nexus_server = CONF.wecube.nexus.server.rstrip('/')
                        nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                                         CONF.wecube.nexus.password)
                        artifact_path = self.get_unit_design_artifact_path(unit_design)
                        artifact_repository = CONF.wecube.nexus.repository
                    else:
                        nexus_server = CONF.nexus.server.rstrip('/')
                        nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
                        artifact_path = self.build_local_nexus_path(unit_design)
                        artifact_repository = CONF.nexus.repository
                    with open(filename, 'rb') as fileobj:
                        upload_result = nexus_client.upload(artifact_repository, artifact_path, filename, 'application/octet-stream', fileobj)
                    new_download_url = upload_result['downloadUrl'].replace(nexus_server,
                                                                            CONF.wecube.server.rstrip('/') + '/artifacts')
            if deploy_package is None :
                raise exceptions.PluginError(message=_("invalid deploy package!"))
            # 创建差异化变量，并更新包的绑定字段
            # bound': true, 'key': name, 'diffExpr': 'expr'
            query_keynames = []
            for diff_config in pacakge_app_diffconfigs:
                query_keynames.append(diff_config['key'])
            for diff_config in pacakge_db_diffconfigs:
                query_keynames.append(diff_config['key'])
            all_diff_configs = self._get_diff_configs_by_keyname(list(set(query_keynames)))
            finder = artifact_utils.CaseInsensitiveDict()
            new_diff_configs = {}
            update_diff_configs = {}
            bind_app_diff_configs = set()
            bind_db_diff_configs = set()
            for conf in all_diff_configs:
                finder[conf['key_name']] = conf
            for diff_conf in pacakge_app_diffconfigs:
                if diff_conf['key'] not in finder:
                    new_diff_configs[diff_conf['key']] = diff_conf
                else:
                    if diff_conf['bound']:
                        bind_app_diff_configs.add(finder[diff_conf['key']]['guid'])
                    update_diff_configs[finder[diff_conf['key']]['guid']] = diff_conf
            for diff_conf in pacakge_db_diffconfigs:
                if diff_conf['key'] not in finder:
                    new_diff_configs[diff_conf['key']] = diff_conf
                else:
                    if diff_conf['bound']:
                        bind_db_diff_configs.add(finder[diff_conf['key']]['guid'])
                    update_diff_configs[finder[diff_conf['key']]['guid']] = diff_conf
            # 创建新的差异化变量项
            if new_diff_configs:
                cmdb_client = self.get_cmdb_client()
                cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [{
                    'code': key,
                    'variable_name': key,
                    'description': key,
                    'variable_value': value.get('diffExpr', ''),
                    'variable_type': self._conv_diff_conf_type(value.get('type', ''))
                } for key,value in new_diff_configs.items()])
                # 新创建的差异化变量也需要检测是否需要绑定
                all_diff_configs = self._get_diff_configs_by_keyname(list(new_diff_configs.keys()))
                for conf in all_diff_configs:
                    finder[conf['key_name']] = conf
                for diff_conf in pacakge_app_diffconfigs:
                    if diff_conf['key'] in finder and diff_conf['bound']:
                        bind_app_diff_configs.add(finder[diff_conf['key']]['guid'])
                for diff_conf in pacakge_db_diffconfigs:
                    if diff_conf['key'] in finder and diff_conf['bound']:
                        bind_db_diff_configs.add(finder[diff_conf['key']]['guid'])
            if update_diff_configs:
                cmdb_client = self.get_cmdb_client()
                cmdb_client.update(CONF.wecube.wecmdb.citypes.diff_config, [{
                    'guid': key,
                    'variable_value': value['diffExpr']
                } for key,value in update_diff_configs.items()])
            # 创建CMDB 包记录
            deploy_package['baseline_package'] =  baseline_package or None
            deploy_package['unit_design'] = unit_design_id
            deploy_package['upload_user'] = force_operator or scoped_globals.GLOBALS.request.auth_user
            deploy_package['upload_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            deploy_package['deploy_package_url'] = new_download_url
            # 更新差异化变量配置
            deploy_package[field_pkg_diff_conf_var_name] = list(bind_app_diff_configs)
            deploy_package[field_pkg_db_diff_conf_var_name] = list(bind_db_diff_configs)
            exist_package = self._get_deploy_package_by_name_unit(deploy_package['name'],unit_design_id)
            if exist_package is None:
                package_result = self.create([deploy_package])
            else:
                deploy_package['guid'] = exist_package['guid']
                package_result = self.pure_update([deploy_package])
            if baseline_package:
                # 基于baseline，更新db upgrade和rollback
                new_package_guid = package_result['data'][0]['guid']
                # upgrade 文件清单仅追加
                file_objs = self.find_files_by_status(
                    baseline_package, new_package_guid,
                    split_to_list(deploy_package[field_pkg_db_upgrade_directory_name]) if deploy_package[field_pkg_db_upgrade_directory_name] else [],
                    ['new', 'changed'])
                filtered_file_objs = []
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            filtered_file_objs.append(f)
                deploy_package[field_pkg_db_upgrade_file_path_name] = FileNameConcater().convert(filtered_file_objs)
                # rollback 文件清单仅追加
                file_objs = self.find_files_by_status(
                    baseline_package, new_package_guid,
                    split_to_list(deploy_package[field_pkg_db_rollback_directory_name]) if deploy_package[field_pkg_db_rollback_directory_name] else [],
                    ['new', 'changed'])
                filtered_file_objs = []
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            filtered_file_objs.append(f)
                deploy_package[field_pkg_db_rollback_file_path_name] = FileNameConcater().convert(filtered_file_objs)
                # update 属性
                deploy_package['guid'] = new_package_guid
                return self.pure_update([deploy_package])['data']
            return package_result['data']
    
    """推送组合物料包[含差异化变量，包配置，包文件] 到nexus
    """    
    def push_compose_package(self, params, unit_design_id:str, deploy_package_id:str):
        filename,fileobj,filesize = self.download_compose_package(deploy_package_id)
        # 新增nexus配置
        nexus_server = CONF.pushnexus.server.rstrip('/')
        nexus_client = nexus.NeuxsClient(CONF.pushnexus.server, CONF.pushnexus.username,
                                            CONF.pushnexus.password)
        artifact_path = '/'
        if params and params.get('path', None):
            artifact_path = params['path']
        else:
            unit_design = self._get_unit_design_by_id(unit_design_id)
            artifact_path = self.get_unit_design_artifact_path(unit_design)
        artifact_repository = CONF.pushnexus.repository
        upload_result = nexus_client.upload(artifact_repository, artifact_path, os.path.basename(filename), 'application/octet-stream', fileobj)
        return upload_result
    
    """导出组合物料包[含差异化变量，包配置，包文件]
    """    
    def download_compose_package(self, deploy_package_id:str):
        pack_fileobj = tempfile.NamedTemporaryFile()
        pack_filename = self._pack_compose_package(pack_fileobj.name, deploy_package_id)
        pack_fileobj.seek(0, os.SEEK_END)  # 从当前位置（2）移动到文件末尾
        # 获取文件指针当前位置，即文件的大小
        pack_filesize = pack_fileobj.tell()
        pack_fileobj.seek(0, os.SEEK_SET)
        return pack_filename,pack_fileobj,pack_filesize
    
    def _get_deploy_package_by_id(self, deploy_package_id: str):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": deploy_package_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        return resp_json['data']['contents'][0]

    def _get_deploy_package_by_name_unit(self, pkg_name: str, unit_design_id: str):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "name",
                "operator": "eq",
                "value": pkg_name
            },{
                "name": "unit_design",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            return None
        return resp_json['data']['contents'][0]

    def _get_unit_design_by_id(self, unit_design_id: str):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        return resp_json['data']['contents'][0]

    def _get_diff_configs_by_keyname(self, key_names):
        cmdb_client = self.get_cmdb_client()
        if key_names:
            diff_config_query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "key_name",
                    "operator": "in",
                    "value": key_names
                }],
                "paging": False
            }
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for key_names [%(names)s]") %
                                           {'names': key_names})
            return resp_json['data']['contents']
        return []
    
    def _pack_compose_package(self, pack_filepath, deploy_package_id:str):
        deploy_package = self._get_deploy_package_by_id(deploy_package_id)
        deploy_package_url = deploy_package['deploy_package_url']

        # 整理部署包数据
        # 上传时需要替换的值：unit_design，deploy_package_url，upload_user，upload_time
        del deploy_package['guid']
        del deploy_package['key_name']
        del deploy_package['nextOperations']
        del deploy_package['baseline_package']
        del deploy_package['create_time']
        del deploy_package['create_user']
        del deploy_package['update_time']
        del deploy_package['update_user']
        del deploy_package['upload_user']
        del deploy_package['upload_time']
        del deploy_package['unit_design']
        del deploy_package['confirm_time']
        del deploy_package['deploy_package_url']
        del deploy_package[field_pkg_diff_conf_var_name]
        del deploy_package[field_pkg_db_diff_conf_var_name]
        # 整理差异化变量
        # 处理diff_conf_variable && db_diff_conf_variable
        deploy_package_detail = self.get(None, deploy_package_id)
        package_app_diff_configs = deploy_package_detail.get(field_pkg_diff_conf_var_name, []) or []
        package_db_diff_configs = deploy_package_detail.get(field_pkg_db_diff_conf_var_name, []) or []
        package_app_diff_configs = [{'bound': d['bound'], 'key':d['key'], 'diffExpr':d['diffExpr'], 'type': d['type']} for d in package_app_diff_configs]
        package_db_diff_configs = [{'bound': d['bound'], 'key':d['key'], 'diffExpr':d['diffExpr'], 'type': d['type']} for d in package_db_diff_configs]
        # 下载原包文件
        with tempfile.TemporaryDirectory() as tmp_path:
            package_path_file = self.download_from_url(tmp_path, deploy_package_url)
            package_path_data = os.path.join(tmp_path, 'package.json')
            with open(package_path_data, 'w') as f:
                content = json.dumps(deploy_package)
                f.write(content)
            package_path_app_diffconfigs = os.path.join(tmp_path, 'package_app_diffconfigs.json')
            with open(package_path_app_diffconfigs, 'w') as f:
                content = json.dumps(package_app_diff_configs)
                f.write(content)
            package_path_db_diffconfigs = os.path.join(tmp_path, 'package_db_diffconfigs.json')
            with open(package_path_db_diffconfigs, 'w') as f:
                content = json.dumps(package_db_diff_configs)
                f.write(content)
            # 指定输出的 tar.gz 文件名
            clean_filename = os.path.splitext(os.path.splitext(os.path.basename(package_path_file))[0])[0]
            output_filename = os.path.join(tmp_path, '[W]'+clean_filename + '_weart.tar.gz')
            # 创建压缩文件
            with tarfile.open(pack_filepath, "w:gz") as tar:
                tar.add(package_path_file, arcname=os.path.basename(package_path_file))
                tar.add(package_path_data, arcname=os.path.basename(package_path_data))
                tar.add(package_path_app_diffconfigs, arcname=os.path.basename(package_path_app_diffconfigs))
                tar.add(package_path_db_diffconfigs, arcname=os.path.basename(package_path_db_diffconfigs))
        return output_filename

    def upload(self, filename, filetype, fileobj, baseline_package, unit_design_id):
        if not is_upload_local_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        if self._is_compose_package(filename):
            return self.upload_compose_package(filename, fileobj, unit_design_id,baseline_package=baseline_package)
        unit_design = self._get_unit_design_by_id(unit_design_id)
        nexus_server = None
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            nexus_server = CONF.wecube.nexus.server.rstrip('/')
            nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                             CONF.wecube.nexus.password)
            artifact_path = self.get_unit_design_artifact_path(unit_design)
            artifact_repository = CONF.wecube.nexus.repository
        else:
            nexus_server = CONF.nexus.server.rstrip('/')
            nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
            artifact_path = self.build_local_nexus_path(unit_design)
            artifact_repository = CONF.nexus.repository
        upload_result = nexus_client.upload(artifact_repository, artifact_path, filename, filetype, fileobj)
        new_download_url = upload_result['downloadUrl'].replace(nexus_server,
                                                                CONF.wecube.server.rstrip('/') + '/artifacts')
        package_rows = [{
            'baseline_package': baseline_package or None,
            'name': filename,
            'code': filename,
            'deploy_package_url': new_download_url,
            'md5_value': calculate_md5(fileobj),
            field_pkg_is_decompression_name: field_pkg_is_decompression_default_value,
            'upload_user': scoped_globals.GLOBALS.request.auth_user,
            'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'unit_design': unit_design_id
        }]
        exist_package = self._get_deploy_package_by_name_unit(filename,unit_design_id)
        if exist_package is None:
            package_result = self.create(package_rows)
        else:
            package_rows[0]['guid'] = exist_package['guid']
            package_result = self.pure_update(package_rows)
        new_package_guid = package_result['data'][0]['guid']
        new_deploy_attrs = self._analyze_package_attrs(new_package_guid, baseline_package, {})
        # update 属性
        new_deploy_attrs['guid'] = new_package_guid
        self.pure_update([new_deploy_attrs])
        return [self._get_deploy_package_by_id(new_package_guid)]

    def upload_from_nexus(self, download_url, baseline_package, unit_design_id):
        if not is_upload_nexus_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        url_info = self.download_url_parse(download_url)
        if self._is_compose_package(url_info['filename']):
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
                        return self.upload_compose_package(url_info['filename'], tmp_file, unit_design_id, baseline_package=baseline_package)
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            # 更新unit_design.artifact_path && package.create 即上传成功
            
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
                'baseline_package': baseline_package or None,
                'name': url_info['filename'],
                'code': url_info['filename'],
                'deploy_package_url': CONF.wecube.server.rstrip('/') + '/artifacts' + url_info['fullpath'],
                'md5_value': nexus_md5,
                field_pkg_is_decompression_name: field_pkg_is_decompression_default_value,
                'upload_user': scoped_globals.GLOBALS.request.auth_user,
                'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'unit_design': unit_design_id
            }]
            exist_package = self._get_deploy_package_by_name_unit(url_info['filename'],unit_design_id)
            if exist_package is None:
                package_result = self.create(package_rows)
            else:
                package_rows[0]['guid'] = exist_package['guid']
                package_result = self.pure_update(package_rows)
            new_package_guid = package_result['data'][0]['guid']
            new_deploy_attrs = self._analyze_package_attrs(new_package_guid, baseline_package, {})
            # update 属性
            new_deploy_attrs['guid'] = new_package_guid
            self.pure_update([new_deploy_attrs])
            return [self._get_deploy_package_by_id(new_package_guid)]
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
                        'baseline_package': baseline_package or None,
                        'name':
                        filename,
                        'code':
                        filename,
                        'deploy_package_url':
                        upload_result['downloadUrl'].replace(CONF.nexus.server.rstrip('/'),
                                                             CONF.wecube.server.rstrip('/') + '/artifacts'),
                        'md5_value':
                        calculate_md5(fileobj),
                        field_pkg_is_decompression_name: field_pkg_is_decompression_default_value,
                        'upload_user':
                        scoped_globals.GLOBALS.request.auth_user,
                        'upload_time':
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'unit_design':
                        unit_design_id
                    }]
                    exist_package = self._get_deploy_package_by_name_unit(filename,unit_design_id)
                    if exist_package is None:
                        package_result = self.create(package_rows)
                    else:
                        package_rows[0]['guid'] = exist_package['guid']
                        package_result = self.pure_update(package_rows)
                    new_package_guid = package_result['data'][0]['guid']
                    new_deploy_attrs = self._analyze_package_attrs(new_package_guid, baseline_package, {})
                    # update 属性
                    new_deploy_attrs['guid'] = new_package_guid
                    self.pure_update([new_deploy_attrs])
                    return [self._get_deploy_package_by_id(new_package_guid)]

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
        ]
        clean_data = crud.ColumnValidator.get_clean_data(validates, data, 'update')
        baseline_package_id = clean_data.get('baselinePackage')
        nexus_path_filename = os.path.basename(clean_data['nexusUrl'])
        baseline_package = self._get_deploy_package_by_id(baseline_package_id)
        url = CONF.wecube.nexus.server.rstrip(
            '/') + '/repository/' + CONF.wecube.nexus.repository + '/' + clean_data['nexusUrl'].lstrip('/')
        unit_design_id = baseline_package['unit_design']['guid']
        new_pakcage = self.upload_from_nexus(url, baseline_package_id, unit_design_id)[0]
        return {'guid': new_pakcage['guid']}

    def upload_and_create2(self, data):
        def _pop_none(d, k):
            if k in d and d[k] is None:
                d.pop(k)

        param_rules = [
            crud.ColumnValidator(field='requestId',
                                 rule=validator.LengthValidator(0, 255),
                                 validate_on=['check:O'],
                                 nullable=True),
            crud.ColumnValidator(field='operator',
                                 rule=validator.LengthValidator(0, 255),
                                 validate_on=['check:O'],
                                 nullable=True),
            crud.ColumnValidator(field='inputs',
                                 rule=validator.TypeValidator(list),
                                 validate_on=['check:M'],
                                 nullable=False),
        ]
        input_rules = [
            crud.ColumnValidator(field='callbackParameter',
                                 rule=validator.LengthValidator(0, 255),
                                 validate_on=['check:O'],
                                 nullable=True),
            crud.ColumnValidator(field='unit_design',
                                 rule=validator.LengthValidator(1, 255),
                                 validate_on=['check:M'],
                                 nullable=False),
            crud.ColumnValidator(field='package_name',
                                 rule=validator.LengthValidator(1, 255),
                                 validate_on=['check:M'],
                                 nullable=False),
            crud.ColumnValidator(field='package_guid',
                                 rule=validator.LengthValidator(0, 255),
                                 validate_on=['check:M'],
                                 nullable=False),
            crud.ColumnValidator(field='baseline_package_guid',
                                 rule=validator.LengthValidator(1, 255),
                                 validate_on=['check:M'],
                                 nullable=False),
        ]

        result = {'resultCode': '0', 'resultMessage': 'success', 'results': {'outputs': []}}
        is_error = False
        error_indexes = []
        try:
            clean_data_outer = crud.ColumnValidator.get_clean_data(param_rules, data, 'check')
            operator = clean_data_outer.get('operator', None) or 'N/A'
            for idx, item in enumerate(clean_data_outer['inputs']):
                single_result = {
                    'callbackParameter': item.get('callbackParameter', None),
                    'errorCode': '0',
                    'errorMessage': 'success',
                    # 'guid': None,
                    # 'deploy_package_url': None
                }
                try:
                    clean_data = crud.ColumnValidator.get_clean_data(input_rules, item, 'check')
                    cmdb_client = self.get_cmdb_client()
                    query = {
                        "dialect": {
                            "queryMode": "new"
                        },
                        "filters": [{
                            "name": "guid",
                            "operator": "eq",
                            "value": clean_data['unit_design']
                        }],
                        "paging": False
                    }
                    resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
                    if not resp_json.get('data', {}).get('contents', []):
                        raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                                            {'rid': clean_data['unit_design']})
                    unit_design = resp_json['data']['contents'][0]
                    if clean_data['package_guid']:
                        # 有package_guid，则更新
                        new_deploy_attrs = self._analyze_package_attrs(clean_data['package_guid'], clean_data['baseline_package_guid'], {})
                        # update 属性
                        new_deploy_attrs['guid'] = clean_data['package_guid']
                        self.pure_update([new_deploy_attrs])
                    else :
                        # 没有package_guid，则创建
                        r_artifact_path = self.get_unit_design_artifact_path(unit_design)
                        if r_artifact_path != '/':
                            group = r_artifact_path.lstrip('/')
                            group = '/' + group.rstrip('/') + '/'
                            r_artifact_path = group
                        download_url = CONF.wecube.nexus.server.rstrip(
                            '/') + '/repository/' + CONF.wecube.nexus.repository + r_artifact_path + clean_data['package_name']
                        self.upload_from_nexus(download_url, clean_data['baseline_package_guid'], clean_data['unit_design'])
                    result['results']['outputs'].append(single_result)
                except Exception as e:
                    single_result['errorCode'] = '1'
                    single_result['errorMessage'] = str(e)
                    result['results']['outputs'].append(single_result)
                    is_error = True
                    error_indexes.append(str(idx + 1))
        except Exception as e:
            result['resultCode'] = '1'
            result['resultMessage'] = str(e)
        if is_error:
            result['resultCode'] = '1'
            result['resultMessage'] = _('Fail to %(action)s [%(num)s] record, detail error in the data block') % dict(
                action='process', num=','.join(error_indexes))
        return result

    # 纯cmdb创建物料包
    def create(self, data:list) -> list:
        cmdb_client = self.get_cmdb_client()
        return cmdb_client.create(CONF.wecube.wecmdb.citypes.deploy_package, data)
    
    # 纯cmdb更新物料包
    def pure_update(self, data:list) -> list:
        cmdb_client = self.get_cmdb_client()
        return cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, data, keep_origin_value=(field_pkg_key_service_code_name,))

    def update(self,
               data,
               unit_design_id,
               deploy_package_id,
               with_detail=True,
               db_upgrade_detect=False,
               db_rollback_detect=False):
        validates = [
            # common
            crud.ColumnValidator('guid', validate_on=['update:M'], rule='1, 36', rule_type='length', nullable=False),
            crud.ColumnValidator('baseline_package', validate_on=['update:O'], nullable=True),
            crud.ColumnValidator(field_pkg_is_decompression_name,
                                 validate_on=['update:O'],
                                 converter=BooleanNomalizedConverter(True),
                                 nullable=True),
            crud.ColumnValidator(field_pkg_package_type_name, validate_on=['update:O'], nullable=True),
            crud.ColumnValidator(field_pkg_key_service_code_name, validate_on=['update:O'], rule=(list, tuple),rule_type='type', nullable=True),
            # app diff conf
            crud.ColumnValidator(field_pkg_diff_conf_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_diff_conf_file_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_diff_conf_var_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type', nullable=False),
            # app script
            crud.ColumnValidator(field_pkg_script_file_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_deploy_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_start_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_stop_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            # app log
            crud.ColumnValidator(field_pkg_log_file_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_log_file_trade_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_log_file_keyword_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_log_file_metric_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_log_file_trace_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            # db diff conf
            crud.ColumnValidator(field_pkg_db_diff_conf_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_db_diff_conf_file_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_db_diff_conf_var_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            # db deploy
            crud.ColumnValidator(field_pkg_db_deploy_file_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_db_deploy_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            # db upgrade 
            crud.ColumnValidator(field_pkg_db_upgrade_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_db_upgrade_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            # db rollback
            crud.ColumnValidator(field_pkg_db_rollback_directory_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
            crud.ColumnValidator(field_pkg_db_rollback_file_path_name, validate_on=['update:O'], rule=(list, tuple), rule_type='type',
                                 converter=FileNameConcater(), nullable=False),
        ]
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": deploy_package_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        data['guid'] = deploy_package_id
        clean_data = crud.ColumnValidator.get_clean_data(validates, data, 'update')
        # FIXME: patch for wecmdb, error update without code
        clean_data['code'] = deploy_package['name']
        # 校验app diff conf扩展名
        available_extensions = split_to_list(CONF.diff_conf_extension)
        if field_pkg_diff_conf_file_name in data:
            for item in data[field_pkg_diff_conf_file_name]:
                matched = False
                for ext in available_extensions:
                    if fnmatch.fnmatch(item['filename'], '*' + ext):
                        matched = True
                        break
                if not matched:
                    raise exceptions.ValidationError(
                        message=_('invalid filename extension: %(filename)s from %(field)s, must be %(options)s') % {
                            'filename': item['filename'],
                            'field': field_pkg_diff_conf_file_name,
                            'options': available_extensions
                        })
        # 校验db diff conf扩展名
        available_extensions = split_to_list(CONF.db_script_extension)
        if field_pkg_db_diff_conf_file_name in data:
            for item in data[field_pkg_db_diff_conf_file_name]:
                matched = False
                for ext in available_extensions:
                    if fnmatch.fnmatch(item['filename'], '*' + ext):
                        matched = True
                        break
                if not matched:
                    raise exceptions.ValidationError(
                        message=_('invalid filename extension: %(filename)s from %(field)s, must be %(options)s') % {
                            'filename': item['filename'],
                            'field': field_pkg_db_diff_conf_file_name,
                            'options': available_extensions
                        })
        # 兼容提取baseline_package值
        if 'baseline_package' in clean_data:
            # 兼容旧接口传{}/''/null代表清空的情况
            if isinstance(clean_data['baseline_package'], dict):
                if not clean_data['baseline_package']:
                    clean_data['baseline_package'] = None
                else:
                    clean_data['baseline_package'] = clean_data['baseline_package'].get('guid', None)
            elif isinstance(clean_data['baseline_package'], str) and not clean_data['baseline_package']:
                clean_data['baseline_package'] = None
            # FIXME: CMDB 接口仅支持传''表示清空
            if clean_data['baseline_package'] is None:
                clean_data['baseline_package'] = ''
        # 根据用户指定进行变量绑定
        auto_bind = True
        if field_pkg_diff_conf_var_name in data:
            clean_data[field_pkg_diff_conf_var_name] = [c['diffConfigGuid'] for c in data[field_pkg_diff_conf_var_name] if c['bound']]
            auto_bind = False
        # 根据diff_conf_file计算变量进行更新绑定
        if field_pkg_diff_conf_file_name in data and auto_bind:
            bind_variables, new_create_variables = self._analyze_diff_var(deploy_package['guid'], deploy_package['deploy_package_url'], 
                                   deploy_package[field_pkg_diff_conf_file_name], data[field_pkg_diff_conf_file_name])
            if bind_variables is not None:
                clean_data[field_pkg_diff_conf_var_name] = bind_variables
        # db部署支持
        # 根据用户指定进行变量绑定
        db_auto_bind = True
        if field_pkg_db_diff_conf_var_name in data:
            clean_data[field_pkg_db_diff_conf_var_name] = [
                c['diffConfigGuid'] for c in data[field_pkg_db_diff_conf_var_name] if c['bound']
            ]
            db_auto_bind = False
        # 根据diff_conf_file计算变量进行更新绑定
        if field_pkg_db_diff_conf_file_name in data and db_auto_bind:
            bind_variables, new_create_variables = self._analyze_diff_var(deploy_package['guid'], deploy_package['deploy_package_url'], 
                                   deploy_package[field_pkg_db_diff_conf_file_name], data[field_pkg_db_diff_conf_file_name])
            if bind_variables is not None:
                clean_data[field_pkg_db_diff_conf_var_name] = bind_variables
        if db_upgrade_detect:
            clean_data[field_pkg_db_upgrade_file_path_name] = FileNameConcater().convert(
                self.find_files_by_status(
                    clean_data['baseline_package'], deploy_package_id,
                    split_to_list(clean_data[field_pkg_db_upgrade_directory_name]) if clean_data[field_pkg_db_upgrade_directory_name] else [],
                    ['new', 'changed']))
        if db_rollback_detect:
            clean_data[field_pkg_db_rollback_file_path_name] = FileNameConcater().convert(
                self.find_files_by_status(
                    clean_data['baseline_package'], deploy_package_id,
                    split_to_list(clean_data[field_pkg_db_rollback_directory_name]) if clean_data[field_pkg_db_rollback_directory_name] else [],
                    ['new', 'changed']))
        resp_json = cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, [clean_data], keep_origin_value=(field_pkg_key_service_code_name,))
        if with_detail:
            return self.get(unit_design_id, deploy_package_id)
        return resp_json['data']


    def _analyze_diff_var(self, package_id, package_url, origin_conf_list, new_conf_list):
        '''
        conf_list是列表，每个元素是string 或 dict[{configKeyInfos，filename}]
        
        如果返回None表示没有改变不应更新CMDB字段值，否则返回可以用于更新CMDB的variable值(即variable guid 列表)
        '''
        cmdb_client = self.get_cmdb_client()
        new_diff_conf_file_list = set()
        old_diff_conf_file_list = set()
        if new_conf_list and utils.is_string_type(new_conf_list):
            new_conf_list = self.build_file_object(new_conf_list)
        new_diff_conf_file_list = set([f['filename'] for f in new_conf_list])
        if origin_conf_list and utils.is_string_type(origin_conf_list):
            origin_conf_list = self.build_file_object(origin_conf_list)
        old_diff_conf_file_list = set(
            [f['filename'] for f in origin_conf_list])
        # diff_conf_file值并未发生改变，无需下载文件更新变量
        # LOG.debug("new_diff_conf_file_list: %s, old_diff_conf_file_list: %s", new_diff_conf_file_list,old_diff_conf_file_list)
        if new_diff_conf_file_list != old_diff_conf_file_list:
            package_cached_dir = self.ensure_package_cached(package_id,
                                                            package_url)
            self.update_file_variable(package_cached_dir, new_conf_list)
            # LOG.debug("new_conf_list: %s", new_conf_list)
            # 差异化配置项的差异
            package_diff_configs = []
            new_diff_configs = set()
            exist_diff_configs = set()
            for conf_file in new_conf_list:
                package_diff_configs.extend(conf_file['configKeyInfos'])
            query_diff_configs = list(set([p['key'] for p in package_diff_configs]))
            all_diff_configs = self._get_diff_configs_by_keyname(query_diff_configs)
            # if query_diff_configs:
            #     diff_config_query = {
            #         "dialect": {
            #             "queryMode": "new"
            #         },
            #         "filters": [{
            #             "name": "key_name",
            #             "operator": "in",
            #             "value": query_diff_configs
            #         }],
            #         "paging": False
            #     }
            #     resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
            #     all_diff_configs = resp_json['data']['contents']
            finder = artifact_utils.CaseInsensitiveDict()
            new_diff_configs_map = artifact_utils.CaseInsensitiveDict()
            for conf in all_diff_configs:
                finder[conf['key_name']] = conf
            for diff_conf in package_diff_configs:
                if diff_conf['key'] not in finder:
                    new_diff_configs.add(diff_conf['key'])
                    new_diff_configs_map[diff_conf['key']] = diff_conf
                else:
                    exist_diff_configs.add(finder[diff_conf['key']]['guid'])
            # 创建新的差异化变量项
            bind_variables = list(exist_diff_configs)
            new_create_variables = []
            # LOG.debug("new_create_variables: %s", new_create_variables)
            if new_diff_configs:
                # 处理模板替换
                for var_name in new_diff_configs:
                    diff_conf = new_diff_configs_map[var_name]
                    if diff_conf['type'] in field_diff_conf_tpl_map:
                        diff_conf_tpl = field_diff_conf_tpl_map[diff_conf['type']]
                        if diff_conf_tpl:
                            # 替换模板值 $& var_name &$
                            replace_pattern = r'\$&\s*([a-zA-Z0-9_-]+?)\s*\$&'
                            diff_conf['value'] = re.sub(replace_pattern, var_name, diff_conf_tpl)
                resp_json = cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [{
                    'code': c,
                    'variable_name': c,
                    'description': c,
                    'variable_value': new_diff_configs_map.get(c, {}).get('value', ''),
                    'variable_type': self._conv_diff_conf_type(new_diff_configs_map.get(c, {}).get('type', ''))
                } for c in new_diff_configs])
                new_create_variables = [c['guid'] for c in resp_json['data']]
                bind_variables.extend(new_create_variables)
            # LOG.debug("bind_variables: %s", bind_variables)
            return bind_variables, new_create_variables
        return None, None

    def find_files_by_status(self, baseline_id, package_id, source_dirs, status):
        results = []
        files = self.filetree(None, package_id, baseline_id, False, source_dirs, with_dir=False, recursive=True)
        for f in files:
            if f['exists'] and not f['isDir'] and f['comparisonResult'] in status:
                # convert data field
                f['filename'] = f.pop('path', None)
                f.pop('name', None)
                results.append(f)
        results.sort(key=lambda x: x['filename'], reverse=False)
        return results

    def get(self, unit_design_id, deploy_package_id):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": deploy_package_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = (deploy_package.get('baseline_package', None) or {})
        if baseline_package:
            query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "guid",
                    "operator": "eq",
                    "value": baseline_package['guid']
                }],
                "paging": False
            }
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                               {'rid': baseline_package['guid']})
            baseline_package = resp_json['data']['contents'][0]
        result = {}
        result['nextOperations'] = list(set(deploy_package.get('nextOperations', [])))
        result['packageId'] = deploy_package_id
        result['baseline_package'] = baseline_package.get('guid', None)
        # db部署支持
        result[field_pkg_package_type_name] = deploy_package.get(field_pkg_package_type_name,
                                                    constant.PackageType.default) or constant.PackageType.default
        # 文件对比[same, changed, new, deleted]
        baseline_cached_dir = None
        package_cached_dir = None
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                             baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        # common 字段
        result[field_pkg_is_decompression_name] = utils.bool_from_string(deploy_package[field_pkg_is_decompression_name], default=True)
        result[field_pkg_package_type_name] = deploy_package[field_pkg_package_type_name]
        result[field_pkg_key_service_code_name] = deploy_package[field_pkg_key_service_code_name]
        # var 字段
        result[field_pkg_diff_conf_var_name] = deploy_package[field_pkg_diff_conf_var_name]
        result[field_pkg_db_diff_conf_var_name] = deploy_package.get(field_pkg_db_diff_conf_var_name, [])
        # |切割为列表, 更新文件的md5,comparisonResult,isDir
        fields = (field_pkg_diff_conf_directory_name, field_pkg_diff_conf_file_name,
                  field_pkg_script_file_directory_name, field_pkg_deploy_file_path_name, 
                  field_pkg_start_file_path_name, field_pkg_stop_file_path_name,
                  field_pkg_log_file_directory_name)
        for field in fields:
            result[field] = self.build_file_object(deploy_package[field])
            if result[field_pkg_package_type_name] in (constant.PackageType.app, constant.PackageType.mixed):
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        # log仅更新格式
        fields = (field_pkg_log_file_trade_name, field_pkg_log_file_keyword_name,
                  field_pkg_log_file_metric_name, field_pkg_log_file_trace_name,)
        for field in fields:
            result[field] = self.build_file_object(deploy_package[field])
        # db
        fields = (field_pkg_db_deploy_file_directory_name, field_pkg_db_deploy_file_path_name,
                  field_pkg_db_diff_conf_directory_name, field_pkg_db_diff_conf_file_name,
                  field_pkg_db_upgrade_directory_name, field_pkg_db_rollback_file_path_name, 
                  field_pkg_db_rollback_directory_name, field_pkg_db_upgrade_file_path_name,)
        for field in fields:
            result[field] = self.build_file_object(deploy_package.get(field, None))
            if result[field_pkg_package_type_name] in (constant.PackageType.db, constant.PackageType.mixed):
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
                
        package_app_diff_configs = []
        if result[field_pkg_package_type_name] in (constant.PackageType.app, constant.PackageType.mixed):
            # 更新差异化配置文件的变量列表
            self.update_file_variable(package_cached_dir, result[field_pkg_diff_conf_file_name])
            for conf_file in result[field_pkg_diff_conf_file_name]:
                package_app_diff_configs.extend(conf_file['configKeyInfos'])
        package_db_diff_configs = []
        if result[field_pkg_package_type_name] in (constant.PackageType.db, constant.PackageType.mixed):
            # 更新差异化配置文件的变量列表
            self.update_file_variable(package_cached_dir, result[field_pkg_db_diff_conf_file_name])
            for conf_file in result[field_pkg_db_diff_conf_file_name]:
                package_db_diff_configs.extend(conf_file['configKeyInfos'])
        query_diff_configs = []
        query_diff_configs.extend([p['key'] for p in package_app_diff_configs])
        query_diff_configs.extend([p['key'] for p in package_db_diff_configs])
        query_diff_configs = list(set(query_diff_configs))
        all_diff_configs = self._get_diff_configs_by_keyname(query_diff_configs)
        # if query_diff_configs:
        #     diff_config_query = {
        #         "dialect": {
        #             "queryMode": "new"
        #         },
        #         "filters": [{
        #             "name": "key_name",
        #             "operator": "in",
        #             "value": query_diff_configs
        #         }],
        #         "paging": False
        #     }
        #     resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
        #     all_diff_configs = resp_json['data']['contents']
        if package_app_diff_configs:
            # 更新差异化变量bound/diffConfigGuid/diffExpr/fixedDate/key/type
            result[field_pkg_diff_conf_var_name] = self.update_diff_conf_variable(all_diff_configs, package_app_diff_configs,
                                                                          result[field_pkg_diff_conf_var_name])
        if package_db_diff_configs:
            # 更新差异化变量bound/diffConfigGuid/diffExpr/fixedDate/key/type
            result[field_pkg_db_diff_conf_var_name] = self.update_diff_conf_variable(all_diff_configs, package_db_diff_configs,
                                                                             result[field_pkg_db_diff_conf_var_name])
        return result

    def baseline_compare(self, unit_design_id, deploy_package_id, baseline_package_id):
        cmdb_client = self.get_cmdb_client()
        deploy_package = self._get_deploy_package_by_id(deploy_package_id)
        baseline_package = self._get_deploy_package_by_id(baseline_package_id)
        baseline_cached_dir = None
        package_cached_dir = None
        # 确认baseline和package文件已下载并解压缓存在本地(加锁)
        baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                         baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        package_type = baseline_package.get(field_pkg_package_type_name,
                                            constant.PackageType.default) or constant.PackageType.default
        is_decompression = baseline_package.get(field_pkg_is_decompression_name,
                                            field_pkg_is_decompression_default_value) or field_pkg_is_decompression_default_value
        key_service_code = baseline_package.get(field_pkg_key_service_code_name,
                                            field_pkg_key_service_code_default_value) or field_pkg_key_service_code_default_value
        new_deploy_package_attrs = self._analyze_package_attrs(deploy_package_id, baseline_package_id, {
            field_pkg_package_type_name: package_type,
            field_pkg_is_decompression_name: is_decompression,
            field_pkg_key_service_code_name: key_service_code
        })

        result = {}
        result[field_pkg_package_type_name] = package_type
        result[field_pkg_is_decompression_name] = is_decompression
        result[field_pkg_key_service_code_name] = key_service_code
        if package_type in (constant.PackageType.app, constant.PackageType.mixed):
            # |切割为列表
            fields = (field_pkg_diff_conf_directory_name, field_pkg_diff_conf_file_name,
                    field_pkg_script_file_directory_name, field_pkg_deploy_file_path_name, 
                    field_pkg_start_file_path_name, field_pkg_stop_file_path_name,
                    field_pkg_log_file_directory_name)
            for field in fields:
                result[field] = self.build_file_object(new_deploy_package_attrs.get(field, None))
                if package_type in (constant.PackageType.app, constant.PackageType.mixed):
                    # 更新文件的md5,comparisonResult,isDir
                    self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
            fields = (field_pkg_log_file_trade_name, field_pkg_log_file_keyword_name,
                    field_pkg_log_file_metric_name, field_pkg_log_file_trace_name,)
            for field in fields:
                result[field] = self.build_file_object(new_deploy_package_attrs.get(field, None))
        # db部署支持
        if package_type in (constant.PackageType.db, constant.PackageType.mixed):
            fields = (field_pkg_db_deploy_file_directory_name, field_pkg_db_deploy_file_path_name,
                    field_pkg_db_diff_conf_directory_name, field_pkg_db_diff_conf_file_name,
                    field_pkg_db_upgrade_directory_name, field_pkg_db_upgrade_file_path_name,
                    field_pkg_db_rollback_directory_name, field_pkg_db_rollback_file_path_name,)
            for field in fields:
                result[field] = self.build_file_object(new_deploy_package_attrs.get(field, None))
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        return result

    def baseline_files_compare(self, data, unit_design_id, deploy_package_id, baseline_package_id):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": deploy_package_id
            }],
            "paging": False
        }
        self.set_package_query_fields(query)
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = None
        if baseline_package_id:
            query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "guid",
                    "operator": "eq",
                    "value": baseline_package_id
                }],
                "paging": False
            }
            self.set_package_query_fields(query)
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                               {'rid': baseline_package_id})
            baseline_package = resp_json['data']['contents'][0]
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        baseline_cached_dir = None
        package_cached_dir = None
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                             baseline_package['deploy_package_url'])
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

    def _scan_dir(self, basepath, subpath, with_dir=True, recursive=False):
        results = []
        path = os.path.join(basepath, subpath)
        if os.path.exists(path) and os.path.isdir(path):
            if recursive:
                for _root, _dirs, _files in os.walk(path):
                    if with_dir:
                        for d in _dirs:
                            results.append({
                                'children': [],
                                'comparisonResult': None,
                                'exists': True,
                                'isDir': True,
                                'md5': None,
                                'name': d,
                                'path': os.path.join(_root, d)[len(basepath) + 1:],
                            })
                    for f in _files:
                        results.append({
                            'children': [],
                            'comparisonResult': None,
                            'exists': True,
                            'isDir': False,
                            'md5': None,
                            'name': f,
                            'path': os.path.join(_root, f)[len(basepath) + 1:],
                        })
            else:
                for e in os.scandir(path):
                    results.append({
                        'children': [],
                        'comparisonResult': None,
                        'exists': True,
                        'isDir': e.is_dir(),
                        'md5': None,
                        'name': e.name,
                        'path': e.path[len(basepath) + 1:],
                    })
        results.sort(key=lambda x: x['name'], reverse=False)
        return results

    def filetree(self,
                 unit_design_id,
                 deploy_package_id,
                 baseline_package_id,
                 expand_all,
                 files,
                 with_dir=True,
                 recursive=False):

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
                root_nodes.extend(self._scan_dir(basepath, ''))
            else:
                for f in file_list:
                    new_f = f.lstrip('/')
                    parts = new_f.split('/')
                    # filename on root
                    if len(parts) == 1:
                        subpath = ''
                        scan_results = []
                        if (basepath, subpath) not in expanded_dirs:
                            scan_results = self._scan_dir(basepath, subpath)
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
                                    scan_results = self._scan_dir(basepath, subpath)
                                    expanded_dirs.add((basepath, subpath))
                                path_nodes.extend(scan_results)
                                node = _add_children_node(parts[idx], subpath, path_nodes, True)
                                path_nodes = node['children']
                                subpath = os.path.join(subpath, parts[idx])
                        scan_results = []
                        if (basepath, subpath) not in expanded_dirs:
                            scan_results = self._scan_dir(basepath, subpath)
                            expanded_dirs.add((basepath, subpath))
                        path_nodes.extend(scan_results)
                        if filename:
                            _add_children_node(filename, subpath, path_nodes)
            return root_nodes

        def _get_file_list(baseline_path, package_path, file_list, with_dir, recursive):
            results = []
            for f in file_list:
                new_f = f.lstrip('/')
                parts = new_f.split('/')
                subpath = os.path.join(*[p for p in parts if p not in ('', '.', '..')])
                new_file_list = self._scan_dir(package_path, subpath, with_dir=with_dir, recursive=recursive)
                self.update_file_status(None if not baseline_path else baseline_path,
                                        package_path,
                                        new_file_list,
                                        file_key='path')
                results.extend(new_file_list)
            return results

        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": deploy_package_id
            }],
            "paging": False
        }
        self.set_package_query_fields(query)
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': deploy_package_id})
        deploy_package = resp_json['data']['contents'][0]
        baseline_package = None
        if baseline_package_id:
            query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "guid",
                    "operator": "eq",
                    "value": baseline_package_id
                }],
                "paging": False
            }
            self.set_package_query_fields(query)
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                               {'rid': baseline_package_id})
            baseline_package = resp_json['data']['contents'][0]
        baseline_cached_dir = None
        package_cached_dir = None
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                             baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        results = []
        if expand_all:
            results = _generate_tree_from_list(package_cached_dir, files)
            self.update_tree_status(baseline_cached_dir, package_cached_dir, results)
        else:
            results = _get_file_list(baseline_cached_dir,
                                     package_cached_dir,
                                     files,
                                     with_dir=with_dir,
                                     recursive=recursive)
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
        
        files为[{filename: xxx}]格式
        '''
        spliters = []
        if CONF.encrypt_variable_prefix.strip():
            spliters = [s.strip() for s in CONF.encrypt_variable_prefix.split(',')]
        if CONF.file_variable_prefix.strip():
            spliters.extend([s.strip() for s in CONF.file_variable_prefix.split(',')])
        if CONF.default_special_replace.strip():
            spliters.extend([s.strip() for s in CONF.default_special_replace.split(',')])
        if CONF.global_variable_prefix.strip():
            spliters.extend([s.strip() for s in CONF.global_variable_prefix.split(',')])
        spliters = [s for s in spliters if s]
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
            finder[conf['key_name']] = conf
        for pconf in package_diff_configs:
            p_finder[pconf['key']] = pconf
        for bconf in bounded_diff_configs:
            b_finder[bconf['key_name']] = bconf
        for k, v in p_finder.items():
            conf = finder.get(k, None)
            p_conf = p_finder.get(k, None)
            results.append({
                'bound': k in b_finder,
                'diffConfigGuid': None if conf is None else conf['guid'],
                'diffExpr': None if conf is None else conf['variable_value'],
                'fixedDate': None if conf is None else conf['confirm_time'],
                'key': k if conf is None else conf['key_name'],
                'type': None if p_conf is None else p_conf['type']
            })
        return results

    def get_package_cached_path(self, guid):
        cache_dir = CONF.pakcage_cache_dir
        return os.path.join(cache_dir, guid)

    def ensure_package_cached(self, guid, url):
        file_cache_dir = self.get_package_cached_path(guid)
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
        if not url.startswith(CONF.wecube.s3.server_url):
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
            urlinfo = urllib.parse.urlparse(url)
            nexusurlinfo = urllib.parse.urlparse(nexus_server)
            
            new_url = urlinfo._replace(scheme=nexusurlinfo.scheme, netloc=nexusurlinfo.netloc,path=remove_prefix(urlinfo.path,'/artifacts')).geturl()
            # new_url = url.replace(CONF.wecube.server.rstrip('/') + '/artifacts', nexus_server)
            client = nexus.NeuxsClient(nexus_server, nexus_username, nexus_password)
            client.download_file(filepath, url=new_url)
        else:
            client = s3.S3Downloader(url)
            client.download_file(filepath, CONF.wecube.s3.access_key, CONF.wecube.s3.secret_key)
        return filepath

    def _analyze_package_attrs(self, package_id:str, baseline_package_id:str, input_attrs:map, do_bind_vars=True) -> map:
        # input_attrs都是以CMDB字段值方式传递，比如列表实际上是A|B|C格式
        ret_data = {}
        deploy_package = self._get_deploy_package_by_id(package_id)
        # 建议优化为：上传时解压，否则此处会增加耗时
        self.ensure_package_cached(package_id, deploy_package['deploy_package_url'])
        baseline_package = {}
        if baseline_package_id:
            baseline_package = self._get_deploy_package_by_id(baseline_package_id)
            self.ensure_package_cached(baseline_package_id, baseline_package['deploy_package_url'])
        # common
        ret_data[field_pkg_is_decompression_name] = input_attrs.get(field_pkg_is_decompression_name, None) or baseline_package.get(field_pkg_is_decompression_name, field_pkg_is_decompression_default_value) or field_pkg_is_decompression_default_value
        ret_data[field_pkg_package_type_name] = input_attrs.get(field_pkg_package_type_name, None) or baseline_package.get(field_pkg_package_type_name, field_pkg_package_type_default_value) or field_pkg_package_type_default_value
        ret_data[field_pkg_key_service_code_name] = input_attrs.get(field_pkg_key_service_code_name, None) or baseline_package.get(field_pkg_key_service_code_name, field_pkg_key_service_code_default_value) or field_pkg_key_service_code_default_value
        # app diff conf
        FieldSetting = namedtuple("FieldSetting", 'name, default_value')
        fset = FieldSetting(name=field_pkg_diff_conf_directory_name, default_value=field_pkg_diff_conf_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 差异化文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.diff_conf_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_diff_conf_file_name] = FilePathConcater().convert(filtered_file_objs)
                if do_bind_vars:
                    conf_files = self.build_file_object(ret_data[field_pkg_diff_conf_file_name])
                    bind_variables, new_create_variables = self._analyze_diff_var(package_id, deploy_package['deploy_package_url'], 
                                        [], conf_files)
                    if bind_variables is not None:
                        ret_data[field_pkg_diff_conf_var_name] = bind_variables
            else:
                # 差异化文件清单继承删除+继承追加(扩展名限制，去重，保持原顺序)
                baseline_file_value = baseline_package[field_pkg_diff_conf_file_name]
                baseline_file_obj = self.build_file_object(baseline_file_value)
                self.update_file_status(self.get_package_cached_path(baseline_package_id), self.get_package_cached_path(package_id), 
                                        baseline_file_obj, file_key='filename')
                # remove deleted status
                filtered_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] != 'deleted']
                changed_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] == 'changed']
                changed_file_objs_map = set([f['filename'] for f in changed_file_objs])
                # find new,changed status
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                # append new files
                available_extensions = split_to_list(CONF.diff_conf_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            if f['filename'] not in changed_file_objs_map:
                                filtered_file_objs.append(f)
                # filtered_file_objs.sort(key=lambda x: x['filename'], reverse=False)
                ret_data[field_pkg_diff_conf_file_name] = FileNameConcater().convert(filtered_file_objs)
                if do_bind_vars:
                    conf_files = self.build_file_object(ret_data[field_pkg_diff_conf_file_name])
                    bind_variables, new_create_variables = self._analyze_diff_var(package_id, deploy_package['deploy_package_url'], 
                                        [], conf_files)
                    if new_create_variables is not None:
                        bind_variables = [c['guid'] for c in baseline_package[field_pkg_diff_conf_var_name]]
                        bind_variables.extend(new_create_variables)
                        ret_data[field_pkg_diff_conf_var_name] = bind_variables
        else:
            if not baseline_package:
                ret_data[fset.name] = fset.default_value
                # 差异化文件清单自动分析
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.diff_conf_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_diff_conf_file_name] = FilePathConcater().convert(filtered_file_objs)
                if do_bind_vars:
                    conf_files = self.build_file_object(ret_data[field_pkg_diff_conf_file_name])
                    bind_variables, new_create_variables = self._analyze_diff_var(package_id, deploy_package['deploy_package_url'], 
                                        [], conf_files)
                    if bind_variables is not None:
                        ret_data[field_pkg_diff_conf_var_name] = bind_variables
            else:
                base_value = baseline_package[fset.name]
                if not base_value:
                    # 填充默认目录值
                    ret_data[fset.name] = fset.default_value
                else:
                    # 继承baseline值
                    ret_data[fset.name] = base_value
                # 差异化文件清单继承删除+继承追加(扩展名限制，去重，保持原顺序)
                baseline_file_value = baseline_package[field_pkg_diff_conf_file_name]
                baseline_file_obj = self.build_file_object(baseline_file_value)
                self.update_file_status(self.get_package_cached_path(baseline_package_id), self.get_package_cached_path(package_id), 
                                        baseline_file_obj, file_key='filename')
                # remove deleted status
                filtered_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] != 'deleted']
                changed_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] == 'changed']
                changed_file_objs_map = set([f['filename'] for f in changed_file_objs])
                # find new,changed status
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                # append new files
                available_extensions = split_to_list(CONF.diff_conf_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            if f['filename'] not in changed_file_objs_map:
                                filtered_file_objs.append(f)
                # filtered_file_objs.sort(key=lambda x: x['filename'], reverse=False)
                ret_data[field_pkg_diff_conf_file_name] = FileNameConcater().convert(filtered_file_objs)
                if do_bind_vars:
                    conf_files = self.build_file_object(ret_data[field_pkg_diff_conf_file_name])
                    bind_variables, new_create_variables = self._analyze_diff_var(package_id, deploy_package['deploy_package_url'], 
                                        [], conf_files)
                    if new_create_variables is not None:
                        bind_variables = [c['guid'] for c in baseline_package[field_pkg_diff_conf_var_name]]
                        bind_variables.extend(new_create_variables)
                        ret_data[field_pkg_diff_conf_var_name] = bind_variables
        # app bin script
        fset = FieldSetting(name=field_pkg_script_file_directory_name, default_value=field_pkg_script_file_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 无输入则填充默认，否则使用输入值
                ret_data[field_pkg_deploy_file_path_name] = input_attrs.get(field_pkg_deploy_file_path_name, None) or field_pkg_deploy_file_path_default_value
                ret_data[field_pkg_start_file_path_name] = input_attrs.get(field_pkg_start_file_path_name, None) or field_pkg_start_file_path_default_value
                ret_data[field_pkg_stop_file_path_name] = input_attrs.get(field_pkg_stop_file_path_name, None) or field_pkg_stop_file_path_default_value
            else:
                # 无输入则仅继承，否则使用输入值
                ret_data[field_pkg_deploy_file_path_name] = input_attrs.get(field_pkg_deploy_file_path_name, None) or baseline_package[field_pkg_deploy_file_path_name]
                ret_data[field_pkg_start_file_path_name] = input_attrs.get(field_pkg_start_file_path_name, None) or baseline_package[field_pkg_start_file_path_name]
                ret_data[field_pkg_stop_file_path_name] = input_attrs.get(field_pkg_stop_file_path_name, None) or baseline_package[field_pkg_stop_file_path_name]
        else:
            if not baseline_package:
                # 填充默认目录值，脚本文件清单填充默认
                ret_data[fset.name] = fset.default_value
                ret_data[field_pkg_deploy_file_path_name] = field_pkg_deploy_file_path_default_value
                ret_data[field_pkg_start_file_path_name] = field_pkg_start_file_path_default_value
                ret_data[field_pkg_stop_file_path_name] = field_pkg_stop_file_path_default_value
            else:
                # 目录值仅继承，脚本文件清单仅继承
                ret_data[fset.name] = baseline_package[fset.name]
                ret_data[field_pkg_deploy_file_path_name] = baseline_package[field_pkg_deploy_file_path_name]
                ret_data[field_pkg_start_file_path_name] = baseline_package[field_pkg_start_file_path_name]
                ret_data[field_pkg_stop_file_path_name] = baseline_package[field_pkg_stop_file_path_name]
        # app log 
        fset = FieldSetting(name=field_pkg_log_file_directory_name, default_value=field_pkg_log_file_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 无输入则填充默认，否则使用输入值
                ret_data[field_pkg_log_file_trade_name] = input_attrs.get(field_pkg_log_file_trade_name, None) or field_pkg_log_file_trade_default_value
                ret_data[field_pkg_log_file_keyword_name] = input_attrs.get(field_pkg_log_file_keyword_name, None) or field_pkg_log_file_keyword_default_value
                ret_data[field_pkg_log_file_metric_name] = input_attrs.get(field_pkg_log_file_metric_name, None) or field_pkg_log_file_metric_default_value
                ret_data[field_pkg_log_file_trace_name] = input_attrs.get(field_pkg_log_file_trace_name, None) or field_pkg_log_file_trace_default_value
            else:
                # 无输入则仅继承，否则使用输入值
                ret_data[field_pkg_log_file_trade_name] = input_attrs.get(field_pkg_log_file_trade_name, None) or baseline_package[field_pkg_log_file_trade_name]
                ret_data[field_pkg_log_file_keyword_name] = input_attrs.get(field_pkg_log_file_keyword_name, None) or baseline_package[field_pkg_log_file_keyword_name]
                ret_data[field_pkg_log_file_metric_name] = input_attrs.get(field_pkg_log_file_metric_name, None) or baseline_package[field_pkg_log_file_metric_name]
                ret_data[field_pkg_log_file_trace_name] = input_attrs.get(field_pkg_log_file_trace_name, None) or baseline_package[field_pkg_log_file_trace_name]
        else:
            if not baseline_package:
                # 填充默认目录值，日志文件清单填充默认
                ret_data[fset.name] = fset.default_value
                ret_data[field_pkg_log_file_trade_name] = field_pkg_log_file_trade_default_value
                ret_data[field_pkg_log_file_keyword_name] = field_pkg_log_file_keyword_default_value
                ret_data[field_pkg_log_file_metric_name] = field_pkg_log_file_metric_default_value
                ret_data[field_pkg_log_file_trace_name] = field_pkg_log_file_trace_default_value
            else:
                # 目录值仅继承，日志文件清单仅继承
                ret_data[fset.name] = baseline_package[fset.name]
                ret_data[field_pkg_log_file_trade_name] = baseline_package[field_pkg_log_file_trade_name]
                ret_data[field_pkg_log_file_keyword_name] = baseline_package[field_pkg_log_file_keyword_name]
                ret_data[field_pkg_log_file_metric_name] = baseline_package[field_pkg_log_file_metric_name]
                ret_data[field_pkg_log_file_trace_name] = baseline_package[field_pkg_log_file_trace_name]
        # db diff 数据库差异化文件不继承
        fset = FieldSetting(name=field_pkg_db_diff_conf_directory_name, default_value=field_pkg_db_diff_conf_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            # 无输入则填充默认，否则使用输入值
            ret_data[field_pkg_db_diff_conf_file_name] = input_attrs.get(field_pkg_db_diff_conf_file_name, None) or field_pkg_db_diff_conf_file_default_value
        else:
            if not baseline_package:
                # 填充默认目录值，差异化文件清单填充默认(空)
                ret_data[fset.name] = fset.default_value
                ret_data[field_pkg_db_diff_conf_file_name] = field_pkg_db_diff_conf_file_default_value
            else:
                # 目录值仅继承，差异化文件清单填充默认(空)
                ret_data[fset.name] = baseline_package[fset.name]
                ret_data[field_pkg_db_diff_conf_file_name] = field_pkg_db_diff_conf_file_default_value
        # db install
        fset = FieldSetting(name=field_pkg_db_deploy_file_directory_name, default_value=field_pkg_db_deploy_file_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_deploy_file_path_name] = FilePathConcater().convert(filtered_file_objs)
            else:
                # 文件清单继承追加
                baseline_file_value = baseline_package[field_pkg_db_deploy_file_path_name]
                baseline_file_obj = self.build_file_object(baseline_file_value)
                self.update_file_status(self.get_package_cached_path(baseline_package_id), self.get_package_cached_path(package_id), 
                                        baseline_file_obj, file_key='filename')
                changed_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] == 'changed']
                changed_file_objs_map = set([f['filename'] for f in changed_file_objs])
                # find new,changed status
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            if f['filename'] not in changed_file_objs_map:
                                baseline_file_obj.append(f)
                # baseline_file_obj.sort(key=lambda x: x['filename'], reverse=False)
                ret_data[field_pkg_db_deploy_file_path_name] = FileNameConcater().convert(baseline_file_obj)
        else:
            if not baseline_package:
                # 填充默认目录值
                ret_data[fset.name] = fset.default_value
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_deploy_file_path_name] = FilePathConcater().convert(filtered_file_objs)
            else:
                # 目录值仅继承
                ret_data[fset.name] = baseline_package[fset.name]
                base_value = baseline_package[fset.name]
                if not base_value:
                    # 填充默认目录值
                    ret_data[fset.name] = fset.default_value
                # 文件清单继承追加
                baseline_file_value = baseline_package[field_pkg_db_deploy_file_path_name]
                baseline_file_obj = self.build_file_object(baseline_file_value)
                self.update_file_status(self.get_package_cached_path(baseline_package_id), self.get_package_cached_path(package_id), 
                                        baseline_file_obj, file_key='filename')
                changed_file_objs = [f for f in baseline_file_obj if f['comparisonResult'] == 'changed']
                changed_file_objs_map = set([f['filename'] for f in changed_file_objs])
                # find new,changed status
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            if f['filename'] not in changed_file_objs_map:
                                baseline_file_obj.append(f)
                # baseline_file_obj.sort(key=lambda x: x['filename'], reverse=False)
                ret_data[field_pkg_db_deploy_file_path_name] = FileNameConcater().convert(baseline_file_obj)
        # db upgrade
        fset = FieldSetting(name=field_pkg_db_upgrade_directory_name, default_value=field_pkg_db_upgrade_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_upgrade_file_path_name] = FilePathConcater().convert(filtered_file_objs)
                # 目录有输入，没有baseline，脚本文件应当为空
                # ret_data[field_pkg_db_upgrade_file_path_name] = field_pkg_db_upgrade_file_path_default_value
            else:
                # 文件清单仅追加
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                filtered_file_objs = []
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_upgrade_file_path_name] = FileNameConcater().convert(filtered_file_objs)
        else:
            if not baseline_package:
                # 填充默认目录值
                ret_data[fset.name] = fset.default_value
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_upgrade_file_path_name] = FilePathConcater().convert(filtered_file_objs)
                # 目录没有输入，没有baseline，脚本文件应当为空
                # ret_data[field_pkg_db_upgrade_file_path_name] = field_pkg_db_upgrade_file_path_default_value
            else:
                # 目录值仅继承
                ret_data[fset.name] = baseline_package[fset.name]
                base_value = baseline_package[fset.name]
                if not base_value:
                    ret_data[field_pkg_db_upgrade_file_path_name] = field_pkg_db_upgrade_file_path_default_value
                else:
                    # 已继承baseline值
                    # 文件清单仅追加
                    file_objs = self.find_files_by_status(
                        baseline_package_id, package_id,
                        split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                        ['new', 'changed'])
                    filtered_file_objs = []
                    # append new files
                    available_extensions = split_to_list(CONF.db_script_extension)
                    for f in file_objs:
                        for ext in available_extensions:
                            if fnmatch.fnmatch(f['filename'], '*' + ext):
                                filtered_file_objs.append(f)
                    ret_data[field_pkg_db_upgrade_file_path_name] = FileNameConcater().convert(filtered_file_objs)
        # db rollback
        fset = FieldSetting(name=field_pkg_db_rollback_directory_name, default_value=field_pkg_db_rollback_directory_default_value)
        if input_attrs.get(fset.name, None):
            ret_data[fset.name] = input_attrs[fset.name]
            if not baseline_package:
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_rollback_file_path_name] = FilePathConcater().convert(filtered_file_objs)
                # 目录有输入，没有baseline，脚本文件应当为空
                # ret_data[field_pkg_db_rollback_file_path_name] = field_pkg_db_rollback_file_path_default_value
            else:
                # 文件清单仅追加
                file_objs = self.find_files_by_status(
                    baseline_package_id, package_id,
                    split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                    ['new', 'changed'])
                filtered_file_objs = []
                # append new files
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['filename'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_rollback_file_path_name] = FileNameConcater().convert(filtered_file_objs)
        else:
            if not baseline_package:
                # 填充默认目录值
                ret_data[fset.name] = fset.default_value
                # 文件清单自动分析(扩展名限制)
                file_objs = self._scan_dir(self.get_package_cached_path(package_id), ret_data[fset.name], False, True)
                filtered_file_objs = []
                available_extensions = split_to_list(CONF.db_script_extension)
                for f in file_objs:
                    for ext in available_extensions:
                        if fnmatch.fnmatch(f['name'], '*' + ext):
                            filtered_file_objs.append(f)
                ret_data[field_pkg_db_rollback_file_path_name] = FilePathConcater().convert(filtered_file_objs)
                # 目录没有输入，没有baseline，脚本文件应当为空
                # ret_data[field_pkg_db_rollback_file_path_name] = field_pkg_db_rollback_file_path_default_value
            else:
                # 目录值仅继承
                ret_data[fset.name] = baseline_package[fset.name]
                base_value = baseline_package[fset.name]
                if not base_value:
                    ret_data[field_pkg_db_rollback_file_path_name] = field_pkg_db_rollback_file_path_default_value
                else:
                    # 已继承baseline值
                    # 文件清单仅追加
                    file_objs = self.find_files_by_status(
                        baseline_package_id, package_id,
                        split_to_list(ret_data[fset.name]) if ret_data[fset.name] else [],
                        ['new', 'changed'])
                    filtered_file_objs = []
                    # append new files
                    available_extensions = split_to_list(CONF.db_script_extension)
                    for f in file_objs:
                        for ext in available_extensions:
                            if fnmatch.fnmatch(f['filename'], '*' + ext):
                                filtered_file_objs.append(f)
                    ret_data[field_pkg_db_rollback_file_path_name] = FileNameConcater().convert(filtered_file_objs)
        return ret_data
        

class UnitDesignNexusPackages(WeCubeResource):
    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design.get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def list_by_post(self, query, unit_design_id):
        if not is_upload_nexus_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        cmdb_client = self.get_cmdb_client()
        filename = None
        for item in query.get('filters', None) or []:
            if item['name'] == 'filename':
                filename = item['value']
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                         CONF.wecube.nexus.password)
        results = nexus_client.list(CONF.wecube.nexus.repository,
                                    self.get_unit_design_artifact_path(unit_design),
                                    extensions=artifact_utils.REGISTED_UNPACK_FORMATS, filename=filename)
        if not utils.bool_from_string(CONF.nexus_sort_as_string, default=False):
            return self.version_sort(results)
        return sorted(results, key=lambda x: x['name'], reverse=True)

    def version_sort(self, datas):
        def _extract_key(name):
            return tuple([int(i) for i in re.findall('\d+', name)])

        return sorted(datas, key=lambda x: _extract_key(x['name']), reverse=True)
    
    def get(self, unit_design_id):
        cmdb_client = self.get_cmdb_client()
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': unit_design_id})
        unit_design = resp_json['data']['contents'][0]
        return {'artifact_path': self.get_unit_design_artifact_path(unit_design)}

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
        query = {"dialect": {"queryMode": "new"}, "filters": [], "paging": False}
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
        return [i for i in resp_json['data']['contents']]


class OnlyInRemoteNexusPackages(WeCubeResource):

    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design.get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def list_by_post(self, query):
        cmdb_client = self.get_cmdb_client()
        filters = query.get("additionalFilters", None) or []
        unit_design_id = None
        for item in filters:
            if item["attrName"] == "unit_design_id":
                unit_design_id = item["condition"]
                break
        if not unit_design_id:
            return []
            # raise exceptions.NotFoundError(message=_("Unit_design_id can not empty"))

        # get unit_design info
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                                   {'rid': unit_design_id})

        unit_design = resp_json['data']['contents'][0]

        # get cmdb package name
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "unit_design",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }

        cmdb_package_name = set()
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        cmdb_package_list = resp_json.get('data', {}).get('contents', [])
        for item in cmdb_package_list:
            cmdb_package_name.add(item["key_name"])

        # get remote nexus package name
        remote_nexus_package_name = set()
        nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server,
                                         CONF.wecube.nexus.username,
                                         CONF.wecube.nexus.password)
        remote_nexus_package_list = nexus_client.list(CONF.wecube.nexus.repository,
                                                      self.get_unit_design_artifact_path(unit_design))

        for item in remote_nexus_package_list:
            remote_nexus_package_name.add(item["name"])

        result_package_name = remote_nexus_package_name - cmdb_package_name
        result = []
        for item in result_package_name:
            result.append({"id": item, "displayName": item, "unit_design_id": unit_design_id})

        return result
