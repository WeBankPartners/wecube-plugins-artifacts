# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
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

    def _addtional_update(self, session, rid, data, before_updated, after_updated):
        if 'roles' in data:
            current_roles = collections.defaultdict(set)
            for r in after_updated["roles"]:
                current_roles[r['permission']].add(r['role'])

            for perm, perm_roles in data['roles'].items():
                deleted_perm_roles = current_roles[perm] - set(perm_roles)
                new_perm_roles = set(perm_roles) - current_roles[perm]

                for perm_role in new_perm_roles:
                    if not perm_role:
                        continue
                    resource.DiffConfTemplateRole(transaction=session).create({
                        'diff_conf_template_id': after_updated['id'],
                        'role': perm_role,
                        'permission': perm
                    })

                if deleted_perm_roles:
                    resource.DiffConfTemplateRole(transaction=session).delete_all(filters={
                        'diff_conf_template_id': before_updated['id'],
                        'permission': perm,
                        'role': {
                            'in': list(deleted_perm_roles)
                        }
                    })

            # update final roles
            after_updated["roles"] = [
                {"permission": perm, "role": perm_role}
                for perm, perm_roles in data['roles'].items()
                for perm_role in perm_roles
            ]

    def _addtional_list(self, query, filters):
        """权限控制，角色数据过滤"""
        query = super()._addtional_list(query, filters)
        permission_filters = {"roles.role": {'in': list(GLOBALS.request.auth_permissions)}}
        query = self._apply_filters(query, self.orm_meta, permission_filters)
        return query

    def _addtional_count(self, query, filters):
        return self._addtional_list(query, filters)

    def list(self, filters=None, orders=None, offset=None, limit=None, hooks=None):
        """
        补充 is_owner
        """
        results = super().list(filters, orders, offset, limit, hooks)
        for result in results:
            result['is_owner'] = GLOBALS.request.auth_user == result['create_user']
        return results

    def get(self, rid):
        """
        补充 is_owner
        """
        result = super().get(rid)
        if result:
            result['is_owner'] = GLOBALS.request.auth_user == result['create_user']

        return result
