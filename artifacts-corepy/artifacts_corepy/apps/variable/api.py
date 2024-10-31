# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from talos.core import config
from talos.core.i18n import _
from talos.utils.scoped_globals import GLOBALS
from artifacts_corepy.db import resource

from artifacts_corepy.common import exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)
TOKEN_KEY = 'terminal_subsystem_token'


class DiffConfTemplate(resource.DiffConfTemplate):
    def count(self, filters=None, offset=None, limit=None, hooks=None):
        auth_roles = GLOBALS.request.auth_permissions
        filters = filters or {}
        filters['roles.role'] = {'in': list(auth_roles)}
        return super().count(filters=filters, offset=offset, limit=limit, hooks=hooks)

    def list(self, filters=None, orders=None, offset=None, limit=None, hooks=None):
        auth_roles = GLOBALS.request.auth_permissions
        filters = filters or {}
        filters['roles.role'] = {'in': list(auth_roles)}
        refs = super().list(filters=filters, orders=orders, offset=offset, limit=limit, hooks=hooks)
        for ref in refs:
            # process roles
            role_mapping = {'owner': [], 'executor': []}
            for role in ref['roles']:
                role_mapping[role['type']].append(role['role'])
            if set(role_mapping['owner']) & auth_roles:
                ref['is_owner'] = 1
            else:
                ref['is_owner'] = 0
            ref['roles'] = role_mapping
        return refs

    def _addtional_create(self, session, data, created):
        if 'roles' in data:
            refs = data['roles']
            role_owner = refs.get('owner', []) or []
            role_executor = refs.get('executor', []) or []
            ref_groups = [(role_owner, 'owner', resource.BookmarkRole),
                          (role_executor, 'executor', resource.BookmarkRole)]
            for role_refs, ref_type, resource_type in ref_groups:
                reduce_refs = list(set(role_refs))
                reduce_refs.sort(key=role_refs.index)
                if ref_type == 'owner' and len(reduce_refs) == 0:
                    raise exceptions.ValidationError(message=_('length of roles.owner must be >= 1'))
                for ref in reduce_refs:
                    new_ref = {}
                    new_ref['bookmark_id'] = created['id']
                    new_ref['role'] = ref
                    new_ref['type'] = ref_type
                    resource_type(transaction=session).create(new_ref)

    def _addtional_update(self, session, rid, data, before_updated, after_updated):
        if 'roles' in data:
            refs = data['roles']
            role_owner = refs.get('owner', None)
            role_executor = refs.get('executor', None)
            ref_groups = [(role_owner, 'owner', resource.BookmarkRole),
                          (role_executor, 'executor', resource.BookmarkRole)]
            for role_refs, ref_type, resource_type in ref_groups:
                if role_refs is None:
                    continue
                reduce_refs = list(set(role_refs))
                reduce_refs.sort(key=role_refs.index)
                if ref_type == 'owner' and len(reduce_refs) == 0:
                    raise exceptions.ValidationError(message=_('length of roles.owner must be >= 1'))
                old_refs = [
                    result['role'] for result in resource_type(session=session).list(filters={
                        'bookmark_id': before_updated['id'],
                        'type': ref_type
                    })
                ]
                create_refs = list(set(reduce_refs) - set(old_refs))
                create_refs.sort(key=reduce_refs.index)
                delete_refs = set(old_refs) - set(reduce_refs)

                if delete_refs:
                    resource_type(transaction=session).delete_all(filters={
                        'bookmark_id': before_updated['id'],
                        'type': ref_type
                    })
                for ref in create_refs:
                    new_ref = {}
                    new_ref['bookmark_id'] = before_updated['id']
                    new_ref['role'] = ref
                    new_ref['type'] = ref_type
                    resource_type(transaction=session).create(new_ref)

    def update(self, rid, data, filters=None, validate=True, detail=True):
        auth_roles = GLOBALS.request.auth_permissions
        if super().count({'id': rid}) and resource.BookmarkRole().count({
                'bookmark_id': rid,
                'role': {
                    'in': list(auth_roles)
                },
                'type': 'owner'
        }) == 0:
            raise exceptions.ValidationError(message=_('the resource(%(resource)s) does not belong to you') %
                                             {'resource': 'Bookmark[%s]' % rid})
        return super().update(rid, data, filters=filters, validate=validate, detail=detail)

    def delete(self, rid, filters=None, detail=True):
        auth_roles = GLOBALS.request.auth_permissions
        if super().count({'id': rid}) and resource.BookmarkRole().count({
                'bookmark_id': rid,
                'role': {
                    'in': list(auth_roles)
                },
                'type': 'owner'
        }) == 0:
            raise exceptions.ValidationError(message=_('the resource(%(resource)s) does not belong to you') %
                                             {'resource': 'Bookmark[%s]' % rid})
        return super().delete(rid, filters=filters, detail=detail)

