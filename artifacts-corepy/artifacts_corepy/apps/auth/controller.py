# -*- coding: utf-8 -*-
from __future__ import absolute_import

from talos.core.i18n import _
from talos.utils.scoped_globals import GLOBALS

from artifacts_corepy.common import exceptions
from artifacts_corepy.common.mixin import Controller, CollectionController as Collection, ItemController as Item
from artifacts_corepy.apps.auth import api as auth_api


# proxy mode to platform
# from artifacts_corepy.apps.auth import apiv2 as auth_api


class Token(Controller):
    name = 'auth.token'
    resource = auth_api.SysUser
    allow_methods = ('POST',)

    def create(self, req, data, **kwargs):
        return self.make_resource(req).login(data.get('username', ''), data.get('password', ''))


class TokenRefresh(Controller):
    name = 'auth.token'
    resource = auth_api.SysUser
    allow_methods = ('GET',)

    def get(self, req, **kwargs):
        return self.make_resource(req).refresh(GLOBALS.request.auth_token)


class UserMenus(Controller):
    name = 'auth.user-menus'
    resource = auth_api.SysUser
    allow_methods = ('GET',)

    def get(self, req, **kwargs):
        return self.make_resource(req).get_menus(GLOBALS.request.auth_user)


class UserPassword(Controller):
    name = 'auth.user-password'
    resource = auth_api.SysUser
    allow_methods = ('POST',)

    def create(self, req, data, **kwargs):
        return self.make_resource(req).update_password(GLOBALS.request.auth_user, data.get('newPassword', ''),
                                                       data.get('oldPassword', ''))


class User(Collection):
    name = 'auth.users'
    resource = auth_api.SysUser


class UserItem(Item):
    name = 'auth.users'
    resource = auth_api.SysUser


class UserItemMenu(Item):
    name = 'auth.users'
    resource = auth_api.SysUser
    allow_methods = ('GET',)

    def get(self, req, rid):
        return self.make_resource(req).get_menus(rid)


class UserItemResetPassword(Controller):
    name = 'auth.users.password'
    resource = auth_api.SysUser
    allow_methods = ('POST',)

    def create(self, req, data, rid):
        data = data or {}
        return self.make_resource(req).reset_password(rid, password=data.get('password', None))


class UserItemRole(Item):
    name = 'auth.users'
    resource = auth_api.SysUser
    allow_methods = ('GET',)

    def get(self, req, rid):
        return self.make_resource(req).get_roles(rid)


class Role(Collection):
    name = 'auth.roles'
    resource = auth_api.SysRole


class RoleItem(Item):
    name = 'auth.roles'
    resource = auth_api.SysRole


class RoleItemMenu(Controller):
    name = 'auth.roles'
    resource = auth_api.SysRole
    allow_methods = ('GET', 'POST')

    def get(self, req, rid):
        return self.make_resource(req).get_menus(rid)

    def create(self, req, data, rid):
        return self.make_resource(req).set_menus(rid, data)


class RoleItemUser(Controller):
    name = 'auth.roles'
    resource = auth_api.SysRole
    allow_methods = ('GET', 'POST')

    def get(self, req, rid):
        return self.make_resource(req).get_users(rid)

    def create(self, req, data, rid):
        return self.make_resource(req).set_users(rid, data)


class Menu(Collection):
    name = 'auth.menus'
    resource = auth_api.SysMenu
    allow_methods = ('GET',)


class MenuItem(Item):
    name = 'auth.menus'
    resource = auth_api.SysMenu
    allow_methods = ('GET',)
