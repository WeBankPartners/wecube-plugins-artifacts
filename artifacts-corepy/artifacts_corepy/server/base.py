# coding=utf-8
"""
artifacts_corepy.server.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供wsgi启动前数据处理能力

"""

from __future__ import absolute_import

import os
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from talos.core import config

from artifacts_corepy.common import utils as plugin_utils

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
                  'nexus_sort_as_string', 'local_nexus_connector_port', 'nexus_connector_port', 'platform_timezone',
                  'system_design_view', 'sub_system_code', 'sub_system_key', 'cleanup_corn', 'cleanup_keep_topn',
                  'cleanup_keep_unit_field', 'delete_op', 'log_level','ci_typeid_app_root_ci', 'ci_typeid_db_root_ci',
                  'ci_typeid_app_template_ci', 'ci_typeid_db_template_ci', 'push_nexus_server',
                  'push_nexus_repository', 'push_nexus_username', 'push_nexus_password')
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
