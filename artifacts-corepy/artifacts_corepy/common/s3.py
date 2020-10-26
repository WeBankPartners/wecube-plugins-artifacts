# coding=utf-8

from __future__ import absolute_import

import logging
import re

import minio
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
        client = minio.Minio(self.host, access_key, secret_key, secure=secure)
        return client.fget_object(self.bucket, self.object_key, filepath)
