# coding=utf-8

from __future__ import absolute_import

import datetime
import logging
import tempfile
import hashlib
from urllib.parse import urlparse

from artifacts_corepy.common import wecmdbv2 as wecmdb
from artifacts_corepy.common import constant
from artifacts_corepy.common import exceptions
from artifacts_corepy.common import nexus
from talos.core import config
from talos.core.i18n import _
from talos.utils import scoped_globals

LOG = logging.getLogger(__name__)
CONF = config.CONF


class Package(object):
    def create_from_image_name(self, image_name, tag, namespace, md5, nexus_url, connector_port, unit_design_id,
                               baseline_package, operator):
        client = wecmdb.WeCMDBClient(CONF.wecube.server, scoped_globals.GLOBALS.request.auth_token)
        url_result = urlparse(nexus_url
                              or (CONF.wecube.nexus.server if CONF.use_remote_nexus_only else CONF.nexus.server))
        namespace = namespace or ''
        deploy_package_url = '%s:%s/%s%s:%s' % (
            url_result.hostname, connector_port or
            (CONF.wecube.nexus.connector_port if CONF.use_remote_nexus_only else CONF.nexus.connector_port),
            namespace + '/' if namespace else '', image_name, tag)
        package_name = '%s-%s' % (image_name, tag)
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "name",
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
        resp_json = client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        exists = resp_json.get('data', {}).get('contents', [])
        package = {'guid': None, 'deploy_package_url': None}
        if not exists:
            data = {
                'baseline_package': baseline_package or '',
                'unit_design': unit_design_id,
                'name': package_name,
                'deploy_package_url': deploy_package_url,
                'md5_value': md5 or 'N/A',
                'package_type': constant.PackageType.image,
                'upload_user': operator,
                'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            ret = client.create(CONF.wecube.wecmdb.citypes.deploy_package, [data])
            package = {'guid': ret['data'][0]['guid'], 'deploy_package_url': ret['data'][0]['deploy_package_url']}
        else:
            package = {'guid': exists[0]['data']['guid'], 'deploy_package_url': exists[0]['data']['deploy_package_url']}
        return package

    def build_local_nexus_path(self, unit_design):
        return unit_design['key_name']

    def get_unit_design_artifact_path(self, unit_design):
        artifact_path = unit_design.get(CONF.wecube.wecmdb.artifact_field, None)
        artifact_path = artifact_path or '/'
        return artifact_path

    def calculate_md5(self, fileobj):
        hasher = hashlib.md5()
        chunk_size = 64 * 1024
        fileobj.seek(0)
        chunk = fileobj.read(chunk_size)
        while chunk:
            hasher.update(chunk)
            chunk = fileobj.read(chunk_size)
        return hasher.hexdigest()

    def create_from_remote(self, package_name, package_guid, unit_design_id, operator):
        cmdb_client = wecmdb.WeCMDBClient(CONF.wecube.server, scoped_globals.GLOBALS.request.auth_token)
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
                md5 = self.calculate_md5(fileobj)
                if not package_guid:
                    data = {
                        'unit_design': unit_design_id,
                        'name': package_name,
                        'deploy_package_url': deploy_package_url,
                        'md5_value': md5 or 'N/A',
                        'upload_user': operator,
                        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    ret = cmdb_client.create(CONF.wecube.wecmdb.citypes.deploy_package, [data])
                    # package = {'guid': ret['data'][0]['guid'],
                    #           'deploy_package_url': ret['data'][0]['deploy_package_url']}
                else:
                    update_data = {
                        'guid': package_guid,
                        'unit_design': unit_design_id,
                        'name': package_name,
                        'deploy_package_url': deploy_package_url,
                        'md5_value': md5 or 'N/A',
                        'upload_user': operator,
                        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    ret = cmdb_client.update(CONF.wecube.wecmdb.citypes.deploy_package, [update_data])
                    # package = {'guid': exists[0]['data']['guid'],
                    #           'deploy_package_url': exists[0]['data']['deploy_package_url']}

