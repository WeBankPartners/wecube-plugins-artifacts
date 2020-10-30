# coding=utf-8

from __future__ import absolute_import

import logging
import re
import os
import urllib3
import certifi

import minio
from artifacts_corepy.common import exceptions
from talos.core.i18n import _

LOG = logging.getLogger(__name__)

R_S3_ENDPOINT = re.compile(
    r'(?P<schema>http|https|s3)://(?P<host>[._-a-zA-Z0-9]+(:(\d+))?)/(?P<bucket>.+?)/(?P<object_key>.+)')


class S3Downloader(object):
    def __init__(self, url):
        self.url = url
        m = R_S3_ENDPOINT.match(url)
        if m:
            result = m.groupdict()
            self.schema = result['schema']
            self.host = result['host']
            self.bucket = result['bucket']
            self.object_key = result['object_key']
        else:
            raise ValueError(_('invalid s3 endpoint url, eg: schema://host[:port]/bucket/object'))

    def download_file(self, filepath, access_key, secret_key):
        secure = True if self.schema == 'https' else False
        ca_certs = os.environ.get('SSL_CERT_FILE') or certifi.where()
        http_client = urllib3.PoolManager(timeout=3,
                                          maxsize=10,
                                          cert_reqs='CERT_REQUIRED',
                                          ca_certs=ca_certs,
                                          retries=urllib3.Retry(total=1,
                                                                backoff_factor=0.2,
                                                                status_forcelist=[500, 502, 503, 504]))
        client = minio.Minio(self.host, access_key, secret_key, secure=secure, http_client=http_client)
        try:
            return client.fget_object(self.bucket, self.object_key, filepath)
        except Exception as e:
            raise exceptions.PluginError(message=_('failed to download file[%(filepath)s] from s3: %(reason)s') % {
                'filepath': self.object_key,
                'reason': str(e)
            })
