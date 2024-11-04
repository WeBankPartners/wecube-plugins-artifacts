# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from talos.core import config
from talos.utils import scoped_globals

from artifacts_corepy.common import wecube

LOG = logging.getLogger(__name__)
CONF = config.CONF


class WeCubeResource(object):
    def __init__(self, server=None, token=None):
        self.server = server or CONF.wecube.server
        self.token = token or scoped_globals.GLOBALS.request.auth_token

    @property
    def platform(self):
        return wecube.WeCubeClient(self.server, self.token)

    def list(self, params):
        pass


class SysUser(WeCubeResource):
    def list(self, params):
        params['filters'] = []
        params['paging'] = False
        return self.platform.get(self.server + '/platform/v1/roles/retrieve', params)
