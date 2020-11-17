# coding=utf-8
"""
artifacts_corepy.server.wsgi_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供wsgi启动能力

"""

from __future__ import absolute_import

import base64
import json
import os
import os.path

from artifacts_corepy.common import utils as plugin_utils
from artifacts_corepy.middlewares import auth
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from talos.core import config, utils
from talos.server import base

# @config.intercept('db_password', 'other_password')
# def get_password(value, origin_value):
#     """value为上一个拦截器处理后的值（若此函数为第一个拦截器，等价于origin_value）
#        origin_value为原始配置文件的值
#        没有拦截的变量talos将自动使用原始值，因此定义一个拦截器是很关键的
#        函数处理后要求必须返回一个值
#     """
#     # 演示使用不安全的base64，请使用你认为安全的算法进行处理
#     return base64.b64decode(origin_value)

RSA_KEY_PATH = '/certs/rsa_key'


def decrypt_rsa(secret_key, encrypt_text):
    rsakey = RSA.importKey(secret_key)
    cipher = Cipher_pkcs1_v1_5.new(rsakey)
    random_generator = Random.new().read
    text = cipher.decrypt(plugin_utils.b64decode_key(encrypt_text), random_generator)
    return text.decode('utf-8')


@config.intercept('upload_enabled', 'upload_nexus_enabled', 'ci_typeid_system_design', 'ci_typeid_unit_design',
                  'ci_typeid_diff_config', 'ci_typeid_deploy_package', 'encrypt_variable_prefix',
                  'file_variable_prefix', 'default_special_replace', 'artifact_field', 's3_access_key', 's3_secret_key',
                  'nexus_server', 'nexus_repository', 'nexus_username', 'nexus_password', 'local_nexus_server',
                  'local_nexus_repository', 'local_nexus_username', 'local_nexus_password', 'gateway_url',
                  'diff_conf_extension', 'variable_expression', 'jwt_signing_key', 'use_remote_nexus_only',
                  'nexus_sort_as_string')
def get_env_value(value, origin_value):
    prefix = 'ENV@'
    encrypt_prefix = 'RSA@'
    if value.startswith(prefix):
        env_name = value[len(prefix):]
        new_value = os.getenv(env_name, default='')
        if new_value.startswith(encrypt_prefix):
            certs_path = RSA_KEY_PATH
            if os.path.exists(certs_path) and os.path.isfile(certs_path):
                with open(certs_path) as f:
                    new_value = decrypt_rsa(f.read(), new_value[len(encrypt_prefix):])
            else:
                raise ValueError('keys with "RSA@", but rsa_key file not exists')
        return new_value
    return value
    # raise ValueError('config intercepter of get_env_value support "ENV@" only')


def error_serializer(req, resp, exception):
    representation = exception.to_dict()
    # replace code with internal application code
    if 'error_code' in representation:
        representation['code'] = representation.pop('error_code')
    representation['status'] = 'ERROR'
    representation['data'] = None
    representation['message'] = representation.pop('description', '')
    resp.body = json.dumps(representation, cls=utils.ComplexEncoder)
    resp.content_type = 'application/json'


application = base.initialize_server('artifacts_corepy',
                                     os.environ.get('ARTIFACTS_COREPY_CONF',
                                                    '/etc/artifacts_corepy/artifacts_corepy.conf'),
                                     conf_dir=os.environ.get('ARTIFACTS_COREPY_CONF_DIR',
                                                             '/etc/artifacts_corepy/artifacts_corepy.conf.d'),
                                     middlewares=[auth.JWTAuth()])
application.set_error_serializer(error_serializer)
