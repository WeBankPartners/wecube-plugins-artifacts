# coding=utf-8
"""
artifacts_corepy.server.wsgi_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供wsgi启动能力

"""

from __future__ import absolute_import

import json
import os
import os.path

from artifacts_corepy.middlewares import auth
from artifacts_corepy.middlewares import permission
from talos.core import utils
from talos.server import base
from artifacts_corepy.server import base as artifacts_base


def error_serializer(req, resp, exception):
    representation = exception.to_dict()
    # replace code with internal application code
    if 'error_code' in representation:
        representation['code'] = representation.pop('error_code')
    representation['status'] = 'ERROR'
    representation['data'] = representation.get('data') or None
    representation['message'] = representation.pop('description', '')
    resp.body = json.dumps(representation, cls=utils.ComplexEncoder)
    resp.content_type = 'application/json'


application = base.initialize_server('artifacts_corepy',
                                     os.environ.get('ARTIFACTS_COREPY_CONF',
                                                    '/etc/artifacts_corepy/artifacts_corepy.conf'),
                                     conf_dir=os.environ.get('ARTIFACTS_COREPY_CONF_DIR',
                                                             '/etc/artifacts_corepy/artifacts_corepy.conf.d'),
                                     middlewares=[auth.JWTAuth(), permission.Permission()])
application.set_error_serializer(error_serializer)
# application.req_options.auto_parse_qs_csv = True
