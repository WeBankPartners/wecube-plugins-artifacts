# -*- coding: utf-8 -*-

from __future__ import absolute_import

from talos.core import config
from talos.core.i18n import _
from artifacts_corepy.apps.variable import controller
from artifacts_corepy.common import wecube
from artifacts_corepy.common import exceptions
from artifacts_corepy.common.wecmdbv2 import URL_PREFIX

CONF = config.CONF


class VariableAdapter(object):
    """差异化变量试算查询"""
    def __call__(self, req, resp, action_name):
        server = CONF.wecube.server
        token = req.auth_token
        client = wecube.WeCubeClient(server, token)
        if action_name == 'render-variable-values':
            ret = client.retrieve(f'{URL_PREFIX}/ci-data/do/Change/app_instance?onlyQuery=true', req.json)
            variable_values = ret['data'][0]['variable_values'] if ret['data'] else ""
            resp.json = {'code': 200, 'status': 'OK', 'data': variable_values, 'message': 'success'}
        else:
            raise exceptions.NotFoundError(
                _('%(action_name)s for variable not supported') % {
                    'action_name': action_name,
                })


def add_routes(api):
    api.add_route('/artifacts/api/v1/diff-conf-templates', controller.CollectionDiffConfTemplates())
    api.add_route('/artifacts/api/v1/diff-conf-templates/{rid}', controller.ItemDiffConfTemplate())
    api.add_sink(
        VariableAdapter(),
        r'/artifacts/api/v1/wecmdb/(?P<action_name>[-_A-Za-z0-9]+)'
    )
