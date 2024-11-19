# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from talos.core import config
from talos.utils.scoped_globals import GLOBALS

from artifacts_corepy.db import resource

from artifacts_corepy.common import exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DiffConfTemplate(resource.DiffConfTemplate):
    def _addtional_create(self, session, data, created):
        if 'roles' in data:
            for perm, perm_roles in data['roles'].items():
                for perm_role in perm_roles:
                    if not perm_role:
                        continue
                    resource.DiffConfTemplateRole(transaction=session).create({
                        'diff_conf_template_id': created['id'],
                        'role': perm_role,
                        'permission': perm
                    })

    def _addtional_list(self, query, filters):
        """权限控制，角色数据过滤"""
        query = super()._addtional_list(query, filters)
        permission_filters = {"roles.role": {'in': list(GLOBALS.request.auth_permissions)}}
        query = self._apply_filters(query, self.orm_meta, permission_filters)
        return query

    def _addtional_count(self, query, filters):
        return self._addtional_list(query, filters)
