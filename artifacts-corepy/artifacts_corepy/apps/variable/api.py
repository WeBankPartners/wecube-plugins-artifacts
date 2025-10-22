# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
import logging
from sqlalchemy import func
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
            # after_updated 可能不包含 roles（为避免 lazy 访问），因此直接查询当前角色表
            db_roles = resource.DiffConfTemplateRole(transaction=session).list({'diff_conf_template_id': rid})
            for r in db_roles:
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

            # 由于 roles 字段的更新不会触发主表的 update_time 自动更新，
            # 需要手动更新主表的 update_time 和 update_user
            session.query(self.orm_meta).filter(self.orm_meta.id == rid).update({
                'update_time': func.now(),
                'update_user': GLOBALS.request.auth_user or None
            })

            # 不主动在 after_updated 上回填 roles，避免再次触发惰性加载

    def _addtional_list(self, query, filters):
        """权限控制，角色数据过滤"""
        query = super()._addtional_list(query, filters)
        
        # 检查是否有 query=all 参数，如果有则跳过权限校验
        request_params = getattr(GLOBALS.request, 'params', {})
        if request_params.get('query') == 'all':
            return query
            
        permission_filters = {"roles.role": {'in': list(GLOBALS.request.auth_permissions)}}
        query = self._apply_filters(query, self.orm_meta, permission_filters)
        return query

    def _addtional_count(self, query, filters):
        """权限控制，角色数据过滤 - 计数方法"""
        query = super()._addtional_count(query, filters)
        
        # 检查是否有 query=all 参数，如果有则跳过权限校验
        request_params = getattr(GLOBALS.request, 'params', {})
        if request_params.get('query') == 'all':
            return query
            
        permission_filters = {"roles.role": {'in': list(GLOBALS.request.auth_permissions)}}
        query = self._apply_filters(query, self.orm_meta, permission_filters)
        return query

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
    
# ... existing code ...

class PrivateVariableTemplate(resource.PrivateVariableTemplate):
    def list(self, filters=None, orders=None, offset=None, limit=None, hooks=None):
        """
        获取私有变量模板列表
        """
        return super().list(filters, orders, offset, limit, hooks)

    def get(self, rid):
        """
        获取单个私有变量模板
        """
        return super().get(rid)

    def create(self, data):
        """
        创建私有变量模板
        """
        return super().create(data)

    def update(self, rid, data):
        """
        更新私有变量模板
        """
        return super().update(rid, data)

    def delete(self, rid):
        """
        删除私有变量模板
        """
        return super().delete(rid)
