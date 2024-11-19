# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import time

import jwt
from talos.core import config, utils
from talos.core.i18n import _
from talos.core import exceptions as core_ex

from artifacts_corepy.common import exceptions
from artifacts_corepy.common import utils as terminal_utils
from artifacts_corepy.db import resource as db_resource

CONF = config.CONF
LOG = logging.getLogger(__name__)


class SysUser(db_resource.SysUser):
    def generate_tokens(self, rid):
        roles = self.get_roles(rid)
        tokens = []
        current_time = int(time.time() * 1000)
        access_token_iat = int(current_time / 1000)
        access_token_exp = access_token_iat + CONF.access_token_exipres
        refresh_token_exp = access_token_iat + CONF.refresh_token_exipres
        decoded_secret = terminal_utils.b64decode_key(CONF.jwt_signing_key)
        tokens.append({
            "expiration": str(current_time + CONF.access_token_exipres * 1000),
            "token": jwt.encode({
                "sub": rid,
                "iat": access_token_iat,
                "type": "accessToken",
                "clientType": "USER",
                "exp": access_token_exp,
                "authority": "[" + ','.join([r['id'] for r in roles]) + "]"
            }, decoded_secret, "HS512").decode(),
            "tokenType": "accessToken"
        })
        tokens.append({
            "expiration": str(current_time + CONF.refresh_token_exipres * 1000),
            "token": jwt.encode({
                "sub": rid,
                "iat": access_token_iat,
                "type": "refreshToken",
                "clientType": "USER",
                "exp": refresh_token_exp
            }, decoded_secret, "HS512",
            ).decode(),
            "tokenType": "refreshToken"
        })
        return tokens

    def login(self, username, password):
        with self.get_session():
            if self.check_password(username, password):
                return self.generate_tokens(username)
            else:
                raise core_ex.LoginError()

    def refresh(self, token):
        with self.get_session():
            try:
                decoded_secret = terminal_utils.b64decode_key(CONF.jwt_signing_key)
                info = jwt.decode(token, key=decoded_secret, verify=True)
                if info['type'] != 'refreshToken':
                    raise core_ex.AuthError()
                return self.generate_tokens(info['sub'])
            except jwt.exceptions.ExpiredSignatureError:
                raise core_ex.AuthError()
            except jwt.exceptions.DecodeError:
                raise core_ex.AuthError()

    def get_menus(self, rid):
        menus = []
        exists = {}
        roles = self.get_roles(rid)
        for role in roles:
            for menu in role['menus']:
                if menu['is_active'] == 'yes' and menu['id'] not in exists:
                    menus.append(menu)
                    exists[menu['id']] = True
        return menus

    def get_roles(self, rid):
        ref = self.get(rid)
        if ref:
            return ref['roles']
        return []

    def create(self, resource, validate=True, detail=True):
        resource['salt'] = utils.generate_salt(16)
        password = utils.generate_salt(16)
        resource['password'] = utils.encrypt_password(password, resource['salt'])
        ref = super().create(resource, validate=validate, detail=detail)
        ref['password'] = password
        return ref

    def reset_password(self, rid, password=None):
        resource = {}
        resource['salt'] = utils.generate_salt(16)
        password = password or utils.generate_salt(16)
        resource['password'] = utils.encrypt_password(password, resource['salt'])
        before_update, after_update = self.update(rid, resource, validate=False)
        if after_update:
            after_update['password'] = password
        return after_update

    def check_password(self, rid, password):
        refs = self.list_internal({'id': rid})
        if refs:
            return utils.check_password(refs[0]['password'], password, refs[0]['salt'])
        return False

    def update_password(self, rid, password, origin_password):
        if not password:
            raise exceptions.PluginError(message=_('unabled to set empty password'))
        if self.check_password(rid, origin_password):
            resource = {}
            resource['salt'] = utils.generate_salt(16)
            password = password or utils.generate_salt(16)
            resource['password'] = utils.encrypt_password(password, resource['salt'])
            before_update, after_update = self.update(rid, resource, validate=False)
            return after_update
        else:
            raise exceptions.PluginError(message=_('faild to set new password: incorrect origin password'))

    def delete(self, rid, filters=None, detail=True):
        refs = self.list({'id': rid})
        if refs and refs[0]['is_system'] == 'yes':
            raise exceptions.PluginError(message=_('unable to delete system user'))
        with self.transaction() as session:
            db_resource.SysRoleUser(transaction=session).delete_all({'user_id': rid})
            return super().delete(rid, filters=filters, detail=detail)


class SysRole(db_resource.SysRole):
    def get_users(self, rid):
        ref = self.get(rid)
        if ref:
            return ref['users']
        return []

    def _update_intersect_refs(self, rid, self_field, ref_field, resource_type, refs, session):
        old_refs = [result[ref_field] for result in resource_type(session=session).list(filters={self_field: rid})]
        create_refs = list(set(refs) - set(old_refs))
        create_refs.sort(key=refs.index)
        delete_refs = set(old_refs) - set(refs)
        if delete_refs:
            resource_type(transaction=session).delete_all(filters={
                self_field: rid,
                ref_field: {
                    'in': list(delete_refs)
                }
            })
        for ref in create_refs:
            new_ref = {}
            new_ref[self_field] = rid
            new_ref[ref_field] = ref
            resource_type(transaction=session).create(new_ref)

    def set_users(self, rid, users):
        with self.transaction() as session:
            self._update_intersect_refs(rid, 'role_id', 'user_id', db_resource.SysRoleUser, users, session)
            return self.get_users(rid)

    def get_menus(self, rid, is_active=True):
        ref = self.get(rid)
        if ref:
            if is_active:
                return [menu for menu in ref['menus'] if menu['is_active'] == 'yes']
            else:
                return ref['menus']
        return []

    def set_menus(self, rid, menus):
        with self.transaction() as session:
            self._update_intersect_refs(rid, 'role_id', 'menu_id', db_resource.SysRoleMenu, menus, session)
            return self.get_menus(rid, is_active=False)

    def delete(self, rid, filters=None, detail=True):
        refs = self.list({'id': rid})
        if refs and refs[0]['is_system'] == 'yes':
            raise exceptions.PluginError(message=_('unable to delete system role'))
        with self.transaction() as session:
            bindings = db_resource.SysRoleUser(transaction=session).list({'role_id': rid})
            if len(bindings) > 0:
                users = ','.join([bind['user_id'] for bind in bindings])
                raise exceptions.PluginError(message=_('role binds with %(users)s') % {'users': users})
            return super().delete(rid, filters=filters, detail=detail)


class SysMenu(db_resource.SysMenu):
    pass
