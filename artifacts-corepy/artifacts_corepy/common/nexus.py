# coding=utf-8
"""
artifacts_corepy.common.nexusclient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目Neuxs Client

"""
import logging
from contextlib import contextmanager

import requests
import requests.auth
from requests_toolbelt import MultipartEncoder
from talos.utils import http

LOG = logging.getLogger(__name__)


class NeuxsClient(object):
    """Neuxs Client"""
    def __init__(self, server, username, password):
        self.server = server.rstrip('/')
        self.username = username
        self.password = password

    def list(self, repository, path, extensions=None, continue_token=None, search_url='/service/rest/v1/search/assets', filename=None):
        results = []
        url = self.server + search_url
        # group必须以/开头且结尾不包含/
        group = path.lstrip('/')
        group = '/' + group.rstrip('/')
        query = {'repository': repository, 'group': group}
        if filename:
            query['q'] = filename
        if continue_token:
            query['continuationToken'] = continue_token
        LOG.info('GET %s', url)
        LOG.debug('Request: %s', str(query))
        resp_json = http.RestfulJson.get(url,
                                         params=query,
                                         auth=requests.auth.HTTPBasicAuth(self.username, self.password))
        LOG.debug('Response: %s', str(resp_json))
        filtered_items = []
        if extensions is not None:
            for i in resp_json['items']:
                for e in extensions:
                    if i['path'].endswith(e):
                        filtered_items.append(i)
        else:
            filtered_items = resp_json['items']
        results.extend([{
            'name': i['path'].split('/')[-1],
            'downloadUrl': i['downloadUrl'],
            'md5': i.get('checksum', {}).get('md5', None) or i.get('checksum', {}).get('sha1', None) or 'N/A',
            'lastModified': i['lastModified'][:19]+'Z' if i.get('lastModified', None) else None,
            'fileSize': i.get('fileSize', 0) or 0
        } for i in filtered_items])
        if resp_json['continuationToken']:
            results.extend(self.list(repository, path, extensions, continue_token=resp_json['continuationToken'], filename=filename))
        return results

    def upload(self, repository, path, filename, filetype, fileobj, upload_url='/service/rest/v1/components'):
        url = self.server + upload_url
        # group必须以/开头且结尾包含/
        group = path.lstrip('/')
        group = '/' + group.rstrip('/') + '/'
        query = {'repository': repository}
        LOG.info('POST %s', url)
        form = {'raw.directory': group, 'raw.asset1.filename': filename}
        LOG.debug('Request: query - %s, form - %s ', str(query), str(form))
        form['raw.asset1'] = (filename, fileobj, filetype)
        stream_form = MultipartEncoder(fields=form)
        resp_json = http.RestfulJson.post(url,
                                          params=query,
                                          data=stream_form,
                                          headers={'Content-Type': stream_form.content_type},
                                          auth=requests.auth.HTTPBasicAuth(self.username, self.password))
        LOG.debug('Response: %s', str(resp_json))
        return {
            'name': filename,
            'downloadUrl': '%(server)s/repository/%(repository)s%(group)s%(filename)s' % {
                'server': self.server,
                'repository': repository,
                'group': group,
                'filename': filename,
            }
        }

    def get_asset(self, repository, group, name, search_url='/service/rest/v1/search/assets'):
        url = self.server + search_url
        # group必须以/开头且结尾不包含/
        group = group.lstrip('/')
        group = '/' + group.rstrip('/')
        query = {'repository': repository, 'group': group, 'name': name}
        LOG.info('GET %s', url)
        LOG.debug('Request: %s', str(query))
        resp_json = http.RestfulJson.get(url,
                                         params=query,
                                         auth=requests.auth.HTTPBasicAuth(self.username, self.password))
        LOG.debug('Response: %s', str(resp_json))
        result = resp_json.get("items", [])
        if not result:
            return {}
        return result[0]

    def delete_assets(self, repository, delete_url):
        url = self.server + delete_url
        LOG.info('DELETE %s', url)
        resp_json = http.RestfulJson.delete(url,
                                            auth=requests.auth.HTTPBasicAuth(self.username, self.password))
        LOG.debug('Response: %s', str(resp_json))

    @contextmanager
    def download_stream(self, url=None, repository=None, path=None):
        new_url = ''
        if url:
            new_url = url
        else:
            new_url = self.server + '/repository/' + repository + '/' + path.lstrip('/')
        LOG.info('GET %s', new_url)
        LOG.debug('Request: ')
        resp = requests.get(new_url, auth=requests.auth.HTTPBasicAuth(self.username, self.password), stream=True)
        resp.raise_for_status()
        yield resp
        LOG.debug('Response: as file stream')

    def download_file(self, filepath, url=None, repository=None, path=None):
        with self.download_stream(url=url, repository=repository, path=path) as resp:
            with open(filepath, 'wb') as f:
                chunk_size = 1024 * 1024
                stream = resp.raw
                chunk = stream.read(chunk_size)
                while chunk:
                    f.write(chunk)
                    chunk = stream.read(chunk_size)
