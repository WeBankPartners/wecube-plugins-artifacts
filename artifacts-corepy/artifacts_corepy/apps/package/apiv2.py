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


def is_upload_local_enabled():
    return utils.bool_from_string(CONF.wecube.upload_enabled)


def is_upload_nexus_enabled():
    return utils.bool_from_string(CONF.wecube.upload_nexus_enabled)


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

    def list_by_post(self, query):
        pass


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
            fields = ('deploy_file_path', 'start_file_path', 'stop_file_path', 'diff_conf_file')
            for field in fields:
                i[field] = self.build_file_object(i.get(field, None))
            # db部署支持
            i['package_type'] = i.get('package_type', constant.PackageType.default) or constant.PackageType.default
            fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                      'db_deploy_file_path', 'db_diff_conf_file')
            for field in fields:
                i[field] = self.build_file_object(i.get(field, None))
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
        ret['group'] = '/' + results[1].rsplit('/', 1)[0]
        return ret
    
    def _is_compose_package(self, filename:str) -> bool:
        if filename.startswith('[W]') and '_weart' in filename:
            return True
        return False
    
    """上传组合物料包[含差异化变量，包配置，包文件]
    """    
    def upload_compose_package(self, compose_filename:str, compose_fileobj, unit_design_id:str, force_operator=None):
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
                    'variable_name': key,
                    'description': key,
                    'variable_value': value['diffExpr']
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
            deploy_package['unit_design'] = unit_design_id
            deploy_package['upload_user'] = force_operator or scoped_globals.GLOBALS.request.auth_user
            deploy_package['upload_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            deploy_package['deploy_package_url'] = new_download_url
            # 更新差异化变量配置
            deploy_package['diff_conf_variable'] = list(bind_app_diff_configs)
            deploy_package['db_diff_conf_variable'] = list(bind_db_diff_configs)
            package_result = self.create([deploy_package])
            return package_result['data']
    
    """推送组合物料包[含差异化变量，包配置，包文件] 到nexus
    """    
    def push_compose_package(self, unit_design_id:str, deploy_package_id:str):
        filename,fileobj,filesize = self.download_compose_package(deploy_package_id)
        # FIXME: 新增nexus配置
        nexus_server = CONF.pushnexus.server.rstrip('/')
        nexus_client = nexus.NeuxsClient(CONF.pushnexus.server, CONF.pushnexus.username,
                                            CONF.pushnexus.password)
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
        del deploy_package['diff_conf_variable']
        del deploy_package['db_diff_conf_variable']
        # 整理差异化变量
        # 处理diff_conf_variable && db_diff_conf_variable
        deploy_package_detail = self.get(None, deploy_package_id)
        package_app_diff_configs = deploy_package_detail.get('diff_conf_variable', []) or []
        package_db_diff_configs = deploy_package_detail.get('db_diff_conf_variable', []) or []
        package_app_diff_configs = [{'bound': d['bound'], 'key':d['key'], 'diffExpr':d['diffExpr']} for d in package_app_diff_configs]
        package_db_diff_configs = [{'bound': d['bound'], 'key':d['key'], 'diffExpr':d['diffExpr']} for d in package_db_diff_configs]
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

    def upload(self, filename, filetype, fileobj, unit_design_id):
        if not is_upload_local_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
        if self._is_compose_package(filename):
            return self.upload_compose_package(filename, fileobj, unit_design_id)
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
            'name': filename,
            'code': filename,
            'deploy_package_url': new_download_url,
            'md5_value': calculate_md5(fileobj),
            'is_decompression': 'true',
            'upload_user': scoped_globals.GLOBALS.request.auth_user,
            'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'unit_design': unit_design_id
        }]
        package_result = self.create(package_rows)
        return package_result['data']

    def upload_from_nexus(self, download_url, unit_design_id):
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
                        return self.upload_compose_package(url_info['filename'], tmp_file, unit_design_id)
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
                'name': url_info['filename'],
                'code': url_info['filename'],
                'deploy_package_url': CONF.wecube.server.rstrip('/') + '/artifacts' + url_info['fullpath'],
                'md5_value': nexus_md5,
                'is_decompression': 'true',
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
                        'code':
                        filename,
                        'deploy_package_url':
                        upload_result['downloadUrl'].replace(CONF.nexus.server.rstrip('/'),
                                                             CONF.wecube.server.rstrip('/') + '/artifacts'),
                        'md5_value':
                        calculate_md5(fileobj),
                        'is_decompression': 'true',
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
            crud.ColumnValidator('packageType',
                                 validate_on=['update:O'],
                                 rule='1, 36',
                                 rule_type='length',
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
            crud.ColumnValidator('dbDiffConfFile',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=True),
        ]
        clean_data = crud.ColumnValidator.get_clean_data(validates, data, 'update')
        baseline_package_id = clean_data.get('baselinePackage')
        nexus_path_filename = os.path.basename(clean_data['nexusUrl'])
        cmdb_client = self.get_cmdb_client()
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
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents', []):
            raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                           {'rid': baseline_package_id})
        baseline_package = resp_json['data']['contents'][0]
        url = CONF.wecube.nexus.server.rstrip(
            '/') + '/repository/' + CONF.wecube.nexus.repository + '/' + clean_data['nexusUrl'].lstrip('/')
        unit_design_id = baseline_package['unit_design']['guid']
        new_pakcage = self.upload_from_nexus(url, unit_design_id)[0]
        if self._is_compose_package(nexus_path_filename):
            update_data = {}
            update_data['baseline_package'] = baseline_package_id
            self.update(update_data,
                    unit_design_id,
                    new_pakcage['guid'],
                    with_detail=False,
                    db_upgrade_detect=False,
                    db_rollback_detect=False)
            return {'guid': new_pakcage['guid']}
        # db部署支持, 检查是否用户手动指定值
        b_db_upgrade_detect = True
        b_db_rollback_detect = True
        update_data = {}
        update_data['baseline_package'] = baseline_package_id
        update_data['is_decompression'] = baseline_package['is_decompression']
        update_data['package_type'] = baseline_package.get(
            'package_type',
            constant.PackageType.default) if clean_data.get('packageType', None) is None else clean_data['packageType']
        keys = [('startFilePath', 'start_file_path'), ('stopFilePath', 'stop_file_path'),
                ('deployFilePath', 'deploy_file_path'), ('diffConfFile', 'diff_conf_file'),
                ('dbUpgradeDirectory', 'db_upgrade_directory'), ('dbRollbackDirectory', 'db_rollback_directory'),
                ('dbUpgradeFilePath', 'db_upgrade_file_path'), ('dbRollbackFilePath', 'db_rollback_file_path'),
                ('dbDeployFilePath', 'db_deploy_file_path'), ('dbDiffConfFile', 'db_diff_conf_file')]
        # 没有指定目录，无法探测
        if (not clean_data.get('db_upgrade_directory', None)) and (not baseline_package.get(
                'db_upgrade_directory', None)):
            b_db_upgrade_detect = False
        if (not clean_data.get('db_rollback_directory', None)) and (not baseline_package.get(
                'db_rollback_directory', None)):
            b_db_rollback_detect = False
        for s_key, d_key in keys:
            if s_key in clean_data and clean_data[s_key] is not None:
                if d_key == 'db_upgrade_file_path':
                    b_db_upgrade_detect = False
                if d_key == 'db_rollback_file_path':
                    b_db_rollback_detect = False
                update_data[d_key] = self.build_file_object(clean_data[s_key])
            else:
                update_data[d_key] = self.build_file_object(baseline_package.get(d_key, None))
        self.update(update_data,
                    unit_design_id,
                    new_pakcage['guid'],
                    with_detail=False,
                    db_upgrade_detect=b_db_upgrade_detect,
                    db_rollback_detect=b_db_rollback_detect)
        return {'guid': new_pakcage['guid']}

    def _create_from_remote(self, package_name, package_guid, unit_design_id, operator, baseline_package_guid):
        # cmdb_client = wecmdb.WeCMDBClient(CONF.wecube.server, scoped_globals.GLOBALS.request.auth_token)
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

        # download package from remote nexus and upload to local nexus
        r_artifact_path = self.get_unit_design_artifact_path(unit_design)
        if r_artifact_path != '/':
            group = r_artifact_path.lstrip('/')
            group = '/' + group.rstrip('/') + '/'
            r_artifact_path = group
        download_url = CONF.wecube.nexus.server.rstrip(
            '/') + '/repository/' + CONF.wecube.nexus.repository + r_artifact_path + package_name
        l_nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
        l_artifact_path = self.build_local_nexus_path(unit_design)
        r_nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                           CONF.wecube.nexus.password)
        if self._is_compose_package(os.path.basename(package_name)):
            with r_nexus_client.download_stream(url=download_url) as resp:
                stream = resp.raw
                chunk_size = 1024 * 1024
                with tempfile.TemporaryFile() as tmp_file:
                    chunk = stream.read(chunk_size)
                    while chunk:
                        tmp_file.write(chunk)
                        chunk = stream.read(chunk_size)
                    tmp_file.seek(0)
                    new_package = self.upload_compose_package(os.path.basename(package_name), tmp_file, unit_design_id, force_operator=operator)
                    update_data = {}
                    update_data['baseline_package'] = baseline_package_guid
                    self.update(update_data,
                            unit_design_id,
                            new_package[0]['guid'],
                            with_detail=False,
                            db_upgrade_detect=False,
                            db_rollback_detect=False)
                    return {'guid': new_package[0]['guid']}
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
                # 用 guid 判断包记录是否存在, 若 guid 为空, 则创建新的记录，否则更新记录
                query = {
                    "dialect": {
                        "queryMode": "new"
                    },
                    "filters": [{
                        "name": "key_name",
                        "operator": "eq",
                        "value": package_name
                    }, {
                        "name": "unit_design",
                        "operator": "eq",
                        "value": unit_design_id
                    }],
                    "paging":
                        False
                }
                # resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
                # exists = resp_json.get('data', {}).get('contents', [])
                deploy_package_url = upload_result['downloadUrl'].replace(CONF.nexus.server.rstrip('/'),
                                                                        CONF.wecube.server.rstrip('/') + '/artifacts')
                md5 = calculate_md5(fileobj)
                if not package_guid:
                    data = {
                        'unit_design': unit_design_id,
                        'name': package_name,
                        'code': package_name,
                        'deploy_package_url': deploy_package_url,
                        'md5_value': md5 or 'N/A',
                        'is_decompression': 'true',
                        'upload_user': operator,
                        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'baseline_package': baseline_package_guid
                    }
                    ret = cmdb_client.create(CONF.wecube.wecmdb.citypes.deploy_package, [data])
                    package = {'guid': ret['data'][0]['guid']}
                    # package = {'guid': ret['data'][0]['guid'],
                    #           'deploy_package_url': ret['data'][0]['deploy_package_url']}
                else:
                    update_data = {
                        'guid': package_guid,
                        'unit_design': unit_design_id,
                        'name': package_name,
                        'code': package_name,
                        'deploy_package_url': deploy_package_url,
                        'md5_value': md5 or 'N/A',
                        'upload_user': operator,
                        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'baseline_package': baseline_package_guid
                    }
                    ret = cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, [update_data])
                    # package = {'guid': exists[0]['data']['guid'],
                    #           'deploy_package_url': exists[0]['data']['deploy_package_url']}
                    package = {'guid': package_guid}
                return package

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
                    baseline_package_id = clean_data.get('baseline_package_guid')
                    cmdb_client = self.get_cmdb_client()
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
                    resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
                    if not resp_json.get('data', {}).get('contents', []):
                        raise exceptions.NotFoundError(message=_("Can not find ci data for guid [%(rid)s]") %
                                                               {'rid': baseline_package_id})
                    baseline_package = resp_json['data']['contents'][0]


                    '''
                    url = CONF.wecube.nexus.server.rstrip(
                        '/') + '/repository/' + CONF.wecube.nexus.repository + '/' + clean_data['nexusUrl'].lstrip('/')
                    unit_design_id = baseline_package['unit_design']['guid']
                    new_pakcage = self.upload_from_nexus(url, unit_design_id)[0]
                    '''
                    unit_design_id = clean_data.get('unit_design')
                    new_pakcage = self._create_from_remote(clean_data['package_name'],
                                                          clean_data['package_guid'],
                                                          clean_data['unit_design'],
                                                          operator,
                                                          clean_data['baseline_package_guid'])
                    if self._is_compose_package(os.path.basename(clean_data['package_name'])):
                        return new_pakcage
                    # db部署支持, 检查是否用户手动指定值
                    b_db_upgrade_detect = True
                    b_db_rollback_detect = True
                    update_data = {}
                    update_data['baseline_package'] = baseline_package_id
                    update_data['is_decompression'] = baseline_package['is_decompression']
                    update_data['package_type'] = baseline_package.get(
                        'package_type',
                        constant.PackageType.default) if clean_data.get('packageType', None) is None else clean_data[
                        'packageType']
                    keys = [('startFilePath', 'start_file_path'), ('stopFilePath', 'stop_file_path'),
                            ('deployFilePath', 'deploy_file_path'), ('diffConfFile', 'diff_conf_file'),
                            ('dbUpgradeDirectory', 'db_upgrade_directory'),
                            ('dbRollbackDirectory', 'db_rollback_directory'),
                            ('dbUpgradeFilePath', 'db_upgrade_file_path'),
                            ('dbRollbackFilePath', 'db_rollback_file_path'),
                            ('dbDeployFilePath', 'db_deploy_file_path'), ('dbDiffConfFile', 'db_diff_conf_file')]
                    # 没有指定目录，无法探测
                    if (not clean_data.get('db_upgrade_directory', None)) and (not baseline_package.get(
                            'db_upgrade_directory', None)):
                        b_db_upgrade_detect = False
                    if (not clean_data.get('db_rollback_directory', None)) and (not baseline_package.get(
                            'db_rollback_directory', None)):
                        b_db_rollback_detect = False
                    for s_key, d_key in keys:
                        if s_key in clean_data and clean_data[s_key] is not None:
                            if d_key == 'db_upgrade_file_path':
                                b_db_upgrade_detect = False
                            if d_key == 'db_rollback_file_path':
                                b_db_rollback_detect = False
                            update_data[d_key] = self.build_file_object(clean_data[s_key])
                        else:
                            update_data[d_key] = self.build_file_object(baseline_package.get(d_key, None))
                    self.update(update_data,
                                unit_design_id,
                                new_pakcage['guid'],
                                with_detail=False,
                                db_upgrade_detect=b_db_upgrade_detect,
                                db_rollback_detect=b_db_rollback_detect)

                    # return {'guid': new_pakcage['guid']}
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
            crud.ColumnValidator('db_diff_conf_file',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 converter=FileNameConcater(),
                                 nullable=False),
            crud.ColumnValidator('db_diff_conf_variable',
                                 validate_on=['update:O'],
                                 rule=(list, tuple),
                                 rule_type='type',
                                 nullable=False),
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
        available_extensions = CONF.diff_conf_extension.split(',')
        if 'diff_conf_file' in data:
            for item in data['diff_conf_file']:
                matched = False
                for ext in available_extensions:
                    if fnmatch.fnmatch(item['filename'], '*' + ext):
                        matched = True
                        break
                if not matched:
                    raise exceptions.ValidationError(
                        message=_('invalid filename extension: %(filename)s from %(field)s, must be %(options)s') % {
                            'filename': item['filename'],
                            'field': 'diff_conf_file',
                            'options': available_extensions
                        })
        if 'db_diff_conf_file' in data:
            for item in data['db_diff_conf_file']:
                matched = False
                for ext in available_extensions:
                    if fnmatch.fnmatch(item['filename'], '*' + ext):
                        matched = True
                        break
                if not matched:
                    raise exceptions.ValidationError(
                        message=_('invalid filename extension: %(filename)s from %(field)s, must be %(options)s') % {
                            'filename': item['filename'],
                            'field': 'db_diff_conf_file',
                            'options': available_extensions
                        })
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
                [f['filename'] for f in self.build_file_object(deploy_package['diff_conf_file'])])
            # diff_conf_file值并未发生改变，无需下载文件更新变量
            if new_diff_conf_file_list != old_diff_conf_file_list:
                package_cached_dir = self.ensure_package_cached(deploy_package['guid'],
                                                                deploy_package['deploy_package_url'])
                self.update_file_variable(package_cached_dir, data['diff_conf_file'])
                # 差异化配置项的差异
                package_diff_configs = []
                new_diff_configs = set()
                exist_diff_configs = set()
                for conf_file in data['diff_conf_file']:
                    package_diff_configs.extend(conf_file['configKeyInfos'])
                query_diff_configs = [p['key'] for p in package_diff_configs]
                all_diff_configs = []
                if query_diff_configs:
                    diff_config_query = {
                        "dialect": {
                            "queryMode": "new"
                        },
                        "filters": [{
                            "name": "key_name",
                            "operator": "in",
                            "value": query_diff_configs
                        }],
                        "paging": False
                    }
                    resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
                    all_diff_configs = resp_json['data']['contents']
                finder = artifact_utils.CaseInsensitiveDict()
                for conf in all_diff_configs:
                    finder[conf['key_name']] = conf
                for diff_conf in package_diff_configs:
                    if diff_conf['key'] not in finder:
                        new_diff_configs.add(diff_conf['key'])
                    else:
                        exist_diff_configs.add(finder[diff_conf['key']]['guid'])
                # 创建新的差异化变量项
                bind_variables = list(exist_diff_configs)
                if new_diff_configs:
                    resp_json = cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [{
                        'variable_name': c,
                        'description': c
                    } for c in new_diff_configs])
                    bind_variables.extend([c['guid'] for c in resp_json['data']])
                if auto_bind:
                    clean_data['diff_conf_variable'] = bind_variables
        # db部署支持
        # 根据用户指定进行变量绑定
        db_auto_bind = True
        if 'db_diff_conf_variable' in data:
            clean_data['db_diff_conf_variable'] = [
                c['diffConfigGuid'] for c in data['db_diff_conf_variable'] if c['bound']
            ]
            db_auto_bind = False
        # 根据diff_conf_file计算变量进行更新绑定
        if 'db_diff_conf_file' in data:
            new_diff_conf_file_list = set([f['filename'] for f in data['db_diff_conf_file']])
            old_diff_conf_file_list = set(
                [f['filename'] for f in self.build_file_object(deploy_package.get('db_diff_conf_file', None))])
            # diff_conf_file值并未发生改变，无需下载文件更新变量
            if new_diff_conf_file_list != old_diff_conf_file_list:
                package_cached_dir = self.ensure_package_cached(deploy_package['guid'],
                                                                deploy_package['deploy_package_url'])
                self.update_file_variable(package_cached_dir, data['db_diff_conf_file'])
                # 差异化配置项的差异
                package_diff_configs = []
                new_diff_configs = set()
                exist_diff_configs = set()
                for conf_file in data['db_diff_conf_file']:
                    package_diff_configs.extend(conf_file['configKeyInfos'])
                query_diff_configs = [p['key'] for p in package_diff_configs]
                all_diff_configs = []
                if query_diff_configs:
                    diff_config_query = {
                        "dialect": {
                            "queryMode": "new"
                        },
                        "filters": [{
                            "name": "key_name",
                            "operator": "in",
                            "value": query_diff_configs
                        }],
                        "paging": False
                    }
                    resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
                    all_diff_configs = resp_json['data']['contents']
                finder = artifact_utils.CaseInsensitiveDict()
                for conf in all_diff_configs:
                    finder[conf['key_name']] = conf
                for diff_conf in package_diff_configs:
                    if diff_conf['key'] not in finder:
                        new_diff_configs.add(diff_conf['key'])
                    else:
                        exist_diff_configs.add(finder[diff_conf['key']]['guid'])
                # 创建新的差异化变量项
                bind_variables = list(exist_diff_configs)
                if new_diff_configs:
                    resp_json = cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [{
                        'variable_name': c,
                        'description': c
                    } for c in new_diff_configs])
                    bind_variables.extend([c['guid'] for c in resp_json['data']])
                if db_auto_bind:
                    clean_data['db_diff_conf_variable'] = bind_variables
        if db_upgrade_detect:
            clean_data['db_upgrade_file_path'] = FileNameConcater().convert(
                self.find_files_by_status(
                    clean_data['baseline_package'], deploy_package_id,
                    clean_data['db_upgrade_directory'].split('|') if clean_data['db_upgrade_directory'] else [],
                    ['new', 'changed']))
        if db_rollback_detect:
            clean_data['db_rollback_file_path'] = FileNameConcater().convert(
                self.find_files_by_status(
                    clean_data['baseline_package'], deploy_package_id,
                    clean_data['db_rollback_directory'].split('|') if clean_data['db_rollback_directory'] else [],
                    ['new', 'changed']))
        resp_json = cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, [clean_data])
        if with_detail:
            return self.get(unit_design_id, deploy_package_id)
        return resp_json['data']

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
        result['package_type'] = deploy_package.get('package_type',
                                                    constant.PackageType.default) or constant.PackageType.default
        # 文件对比[same, changed, new, deleted]
        baseline_cached_dir = None
        package_cached_dir = None
        # 确认baselin和package文件已下载并解压缓存在本地(加锁)
        if baseline_package:
            baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                             baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        # 更新文件的md5,comparisonResult,isDir
        result['is_decompression'] = utils.bool_from_string(deploy_package['is_decompression'], default=True)
        result['diff_conf_variable'] = deploy_package['diff_conf_variable']
        result['db_diff_conf_variable'] = deploy_package.get('db_diff_conf_variable', [])
        # |切割为列表
        fields = ('deploy_file_path', 'start_file_path', 'stop_file_path', 'diff_conf_file')
        for field in fields:
            result[field] = self.build_file_object(deploy_package[field])
            if result['package_type'] in (constant.PackageType.app, constant.PackageType.mixed):
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        package_app_diff_configs = []
        if result['package_type'] in (constant.PackageType.app, constant.PackageType.mixed):
            # 更新差异化配置文件的变量列表
            self.update_file_variable(package_cached_dir, result['diff_conf_file'])
            for conf_file in result['diff_conf_file']:
                package_app_diff_configs.extend(conf_file['configKeyInfos'])

        # db部署支持
        fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                  'db_deploy_file_path', 'db_diff_conf_file')
        for field in fields:
            result[field] = self.build_file_object(deploy_package.get(field, None))
            if result['package_type'] in (constant.PackageType.db, constant.PackageType.mixed):
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        package_db_diff_configs = []
        if result['package_type'] in (constant.PackageType.db, constant.PackageType.mixed):
            # 更新差异化配置文件的变量列表
            self.update_file_variable(package_cached_dir, result['db_diff_conf_file'])
            for conf_file in result['db_diff_conf_file']:
                package_db_diff_configs.extend(conf_file['configKeyInfos'])
        query_diff_configs = []
        query_diff_configs.extend([p['key'] for p in package_app_diff_configs])
        query_diff_configs.extend([p['key'] for p in package_db_diff_configs])
        query_diff_configs = list(set(query_diff_configs))
        all_diff_configs = []
        if query_diff_configs:
            diff_config_query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "key_name",
                    "operator": "in",
                    "value": query_diff_configs
                }],
                "paging": False
            }
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, diff_config_query)
            all_diff_configs = resp_json['data']['contents']
        if package_app_diff_configs:
            # 更新差异化变量bound/diffConfigGuid/diffExpr/fixedDate/key/type
            result['diff_conf_variable'] = self.update_diff_conf_variable(all_diff_configs, package_app_diff_configs,
                                                                          result['diff_conf_variable'])
        if package_db_diff_configs:
            # 更新差异化变量bound/diffConfigGuid/diffExpr/fixedDate/key/type
            result['db_diff_conf_variable'] = self.update_diff_conf_variable(all_diff_configs, package_db_diff_configs,
                                                                             result['db_diff_conf_variable'])
        return result

    def baseline_compare(self, unit_design_id, deploy_package_id, baseline_package_id):
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
        # 确认baseline和package文件已下载并解压缓存在本地(加锁)
        baseline_cached_dir = self.ensure_package_cached(baseline_package['guid'],
                                                         baseline_package['deploy_package_url'])
        package_cached_dir = self.ensure_package_cached(deploy_package['guid'], deploy_package['deploy_package_url'])
        package_type = baseline_package.get('package_type',
                                            constant.PackageType.default) or constant.PackageType.default

        result = {}
        # |切割为列表
        fields = ('deploy_file_path', 'start_file_path', 'stop_file_path', 'diff_conf_file')
        for field in fields:
            result[field] = self.build_file_object(baseline_package.get(field, None))
            if package_type in (constant.PackageType.app, constant.PackageType.mixed):
                # 更新文件的md5,comparisonResult,isDir
                self.update_file_status(baseline_cached_dir, package_cached_dir, result[field])
        # db部署支持
        fields = ('db_upgrade_directory', 'db_rollback_directory', 'db_upgrade_file_path', 'db_rollback_file_path',
                  'db_deploy_file_path', 'db_diff_conf_file')
        for field in fields:
            result[field] = self.build_file_object(baseline_package.get(field, None))
        if package_type in (constant.PackageType.db, constant.PackageType.mixed):
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_upgrade_directory'])
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_rollback_directory'])
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_deploy_file_path'])
            self.update_file_status(baseline_cached_dir, package_cached_dir, result['db_diff_conf_file'])
            result['db_upgrade_file_path'] = self.find_files_by_status(
                baseline_package_id, deploy_package_id, [i['filename'] for i in result['db_upgrade_directory']],
                ['new', 'changed'])
            result['db_rollback_file_path'] = self.find_files_by_status(
                baseline_package_id, deploy_package_id, [i['filename'] for i in result['db_rollback_directory']],
                ['new', 'changed'])
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

    def filetree(self,
                 unit_design_id,
                 deploy_package_id,
                 baseline_package_id,
                 expand_all,
                 files,
                 with_dir=True,
                 recursive=False):
        def _scan_dir(basepath, subpath, with_dir=True, recursive=False):
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

        def _get_file_list(baseline_path, package_path, file_list, with_dir, recursive):
            results = []
            for f in file_list:
                new_f = f.lstrip('/')
                parts = new_f.split('/')
                subpath = os.path.join(*[p for p in parts if p not in ('', '.', '..')])
                new_file_list = _scan_dir(package_path, subpath, with_dir=with_dir, recursive=recursive)
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
        '''
        spliters = [s.strip() for s in CONF.encrypt_variable_prefix.split(',')]
        spliters.extend([s.strip() for s in CONF.file_variable_prefix.split(',')])
        spliters.extend([s.strip() for s in CONF.default_special_replace.split(',')])
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
        artifact_path = unit_design.get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def list_by_post(self, query, unit_design_id):
        if not is_upload_nexus_enabled():
            raise exceptions.PluginError(message=_("Package uploading is disabled!"))
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
        nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                         CONF.wecube.nexus.password)
        results = nexus_client.list(CONF.wecube.nexus.repository,
                                    self.get_unit_design_artifact_path(unit_design),
                                    extensions=artifact_utils.REGISTED_UNPACK_FORMATS)
        if not utils.bool_from_string(CONF.nexus_sort_as_string, default=False):
            return self.version_sort(results)
        return sorted(results, key=lambda x: x['name'], reverse=True)

    def version_sort(self, datas):
        def _extract_key(name):
            return tuple([int(i) for i in re.findall('\d+', name)])

        return sorted(datas, key=lambda x: _extract_key(x['name']), reverse=True)


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
        filters = query["additionalFilters"]
        unit_design_id = None
        for item in filters:
            if item["attrName"] == "unit_design_id":
                unit_design_id = item["condition"]
                break
        if not unit_design_id:
            raise exceptions.NotFoundError(message=_("Unit_design_id can not empty"))

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
