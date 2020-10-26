# coding=utf-8
"""
artifacts_corepy.server.wsgi_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供wsgi启动能力

"""

from __future__ import absolute_import

import base64
import os
import json
from talos.server import base
from talos.core import utils
from talos.core import config

from artifacts_corepy.middlewares import auth

# @config.intercept('db_password', 'other_password')
# def get_password(value, origin_value):
#     """value为上一个拦截器处理后的值（若此函数为第一个拦截器，等价于origin_value）
#        origin_value为原始配置文件的值
#        没有拦截的变量talos将自动使用原始值，因此定义一个拦截器是很关键的
#        函数处理后要求必须返回一个值
#     """
#     # 演示使用不安全的base64，请使用你认为安全的算法进行处理
#     return base64.b64decode(origin_value)


@config.intercept('jwt_signing_key')
def get_env_value(value, origin_value):
    prefix = 'ENV@'
    if value.startswith(prefix):
        env_name = value[len(prefix):]
        return os.getenv(env_name, default='')
    raise ValueError('config intercepter of get_env_value support "ENV@" only')


def error_serializer(req, resp, exception):
    representation = exception.to_dict()
    representation['status'] = 'ERROR'
    representation['data'] = None
    representation['message'] = representation.pop('description')
    resp.body = json.dumps(representation, cls=utils.ComplexEncoder)
    resp.content_type = 'application/json'


application = base.initialize_server('artifacts_corepy',
                                     os.environ.get('ARTIFACTS_COREPY_CONF',
                                                    '/etc/artifacts_corepy/artifacts_corepy.conf'),
                                     conf_dir=os.environ.get('ARTIFACTS_COREPY_CONF_DIR',
                                                             '/etc/artifacts_corepy/artifacts_corepy.conf.d'),
                                     middlewares=[auth.JWTAuth()])
application.set_error_serializer(error_serializer)