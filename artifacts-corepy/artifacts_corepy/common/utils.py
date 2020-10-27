# coding=utf-8
"""
artifacts_corepy.common.config_variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目配置文件的差异化变量解析

"""
import contextlib
import io
import logging
import os.path
import re
import shutil
import tempfile
import time
import requests
import functools
from collections import Mapping, MutableMapping

from talos.core import config
from talos.core import exceptions
from talos.utils import http

try:
    HAS_FCNTL = True
    import fcntl
except:
    HAS_FCNTL = False

LOG = logging.getLogger(__name__)
CONF = config.CONF

# register jar,war,apk as zip file
shutil.register_unpack_format('jar', ['.jar'], shutil._UNPACK_FORMATS['zip'][1])
shutil.register_unpack_format('war', ['.war'], shutil._UNPACK_FORMATS['zip'][1])
shutil.register_unpack_format('apk', ['.apk'], shutil._UNPACK_FORMATS['zip'][1])


def variable_parse(content, spliters):
    variables = []
    rule = re.compile(r'\[(' + '|'.join(spliters) + r')([-_0-9a-zA-Z]+)\]')
    stream = io.StringIO(content)
    lineno = 1
    for line in stream:
        pos = 0
        while pos < len(line):
            result = rule.search(line, pos)
            if result:
                pos = result.end()
                variables.append({'lineno': lineno, 'type': result.group(1), 'name': result.group(2)})
            else:
                pos = len(line)
        lineno += 1
    return variables


def unpack_file(filename, unpack_dest):
    shutil.unpack_archive(filename, unpack_dest)


@contextlib.contextmanager
def lock(name, block=True, timeout=5):
    timeout = 1.0 * timeout
    if HAS_FCNTL:
        acquired = False
        filepath = os.path.join(tempfile.gettempdir(), 'artifacts_lock_%s' % name)
        fp = open(filepath, "a+")
        flag = fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            if not block:
                # non-block yield immediately
                try:
                    fcntl.flock(fp, flag)
                    acquired = True
                except:
                    pass
                yield acquired
            else:
                # block will try until timeout
                time_pass = 0
                while time_pass < timeout:
                    try:
                        fcntl.flock(fp, flag)
                        acquired = True
                        break
                    except:
                        gap = 0.1
                        time.sleep(gap)
                        time_pass += gap
                yield acquired
        finally:
            if acquired:
                fcntl.flock(fp, fcntl.LOCK_UN)
            fp.close()
    else:
        yield False


class CaseInsensitiveDict(dict):
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def __contains__(self, key):
        return key.lower() in self._store

    def has_key(self, key):
        return key.lower() in self._store

    def __repr__(self):
        return str(dict(self.items()))


def json_or_error(func):
    @functools.wraps(func)
    def _json_or_error(url, **kwargs):
        try:
            return func(url, **kwargs)
        except requests.ConnectionError as e:
            LOG.error('http error: %s %s, reason: %s', func.__name__.upper(), url, str(e))
            raise exceptions.CallBackError(message={
                'code': 502,
                'title': 'Connection Error',
                'description': 'Failed to establish a new connection'
            })
        except requests.Timeout as e:
            LOG.error('http error: %s %s, reason: %s', func.__name__.upper(), url, str(e))
            raise exceptions.CallBackError(message={
                'code': 504,
                'title': 'Timeout Error',
                'description': 'Server do not respond'
            })
        except requests.HTTPError as e:
            LOG.error('http error: %s %s, reason: %s', func.__name__.upper(), url, str(e))
            code = int(e.response.status_code)
            message = RestfulJson.get_response_json(e.response, default={'code': code})
            if code == 404:
                message['title'] = 'Not Found'
                message['description'] = 'The resource you request not exist'
            # 如果后台返回的数据不符合要求，强行修正
            if 'code' not in message:
                message['code'] = code
            if 'title' not in message:
                message['title'] = message.get('title', e.response.reason)
            if 'description' not in message:
                message['description'] = message.get('message', str(e))
            raise exceptions.CallBackError(message=message)
        except Exception as e:
            LOG.error('http error: %s %s, reason: %s', func.__name__.upper(), url, str(e))
            message = RestfulJson.get_response_json(e.response,
                                                    default={
                                                        'code': 500,
                                                        'title': 'Server Error',
                                                        'description': str(e)
                                                    })
            if 'code' not in message:
                message['code'] = 500
            if 'title' not in message:
                message['title'] = message.get('title', str(e))
            if 'description' not in message:
                message['description'] = message.get('message', str(e))
            raise exceptions.CallBackError(message=message)

    return _json_or_error


class RestfulJson(object):
    @staticmethod
    def get_response_json(resp, default=None):
        try:
            return resp.json()
        except Exception as e:
            return default

    @staticmethod
    @json_or_error
    def post(url, **kwargs):
        resp = requests.post(url, **kwargs)
        resp.raise_for_status()
        return RestfulJson.get_response_json(resp)

    @staticmethod
    @json_or_error
    def get(url, **kwargs):
        resp = requests.get(url, **kwargs)
        resp.raise_for_status()
        return RestfulJson.get_response_json(resp)

    @staticmethod
    @json_or_error
    def patch(url, **kwargs):
        resp = requests.patch(url, **kwargs)
        resp.raise_for_status()
        return RestfulJson.get_response_json(resp)

    @staticmethod
    @json_or_error
    def delete(url, **kwargs):
        resp = requests.delete(url, **kwargs)
        resp.raise_for_status()
        return RestfulJson.get_response_json(resp)

    @staticmethod
    @json_or_error
    def put(url, **kwargs):
        resp = requests.put(url, **kwargs)
        resp.raise_for_status()
        return RestfulJson.get_response_json(resp)