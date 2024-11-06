# -*- coding: utf-8 -*-
from __future__ import absolute_import

from artifacts_corepy.apps.auth import controller


def add_routes(api):
    # 不需要登陆
    api.add_route('/artifacts/v1/login', controller.Token())
    api.add_route('/artifacts/v1/refresh-token', controller.TokenRefresh())
    # 登陆但不需要权限校验
    api.add_route('/artifacts/v1/user-menus', controller.UserMenus())
    api.add_route('/artifacts/v1/user-password', controller.UserPassword())
    # 登陆且经过权限校验
    api.add_route('/artifacts/v1/users', controller.User())
    api.add_route('/artifacts/v1/users/{rid}', controller.UserItem())
    api.add_route('/artifacts/v1/users/{rid}/reset-password', controller.UserItemResetPassword())
    api.add_route('/artifacts/v1/users/{rid}/menus', controller.UserItemMenu())
    api.add_route('/artifacts/v1/users/{rid}/roles', controller.UserItemRole())
    api.add_route('/artifacts/v1/roles', controller.Role())
    # api.add_route('/artifacts/v1/users/roles', controller.ProxyUserRole())
    # api.add_route('/artifacts/v1/roles', controller.ProxyRole())
    api.add_route('/artifacts/v1/roles/{rid}', controller.RoleItem())
    api.add_route('/artifacts/v1/roles/{rid}/menus', controller.RoleItemMenu())
    api.add_route('/artifacts/v1/roles/{rid}/users', controller.RoleItemUser())
    api.add_route('/artifacts/v1/menus', controller.Menu())
    # api.add_route('/artifacts/v1/menus/{rid}', controller.MenuItem())
