# coding=utf-8

from __future__ import absolute_import

import datetime
import logging
from urllib.parse import urlparse

from artifacts_corepy.common import wecmdb
from talos.core import config
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
                'package_type': 'image',
                'upload_user': operator,
                'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            ret = client.create(CONF.wecube.wecmdb.citypes.deploy_package, [data])
            package = {'guid': ret['data'][0]['guid'], 'deploy_package_url': ret['data'][0]['deploy_package_url']}
        else:
            package = {'guid': exists[0]['data']['guid'], 'deploy_package_url': exists[0]['data']['deploy_package_url']}
        return package
