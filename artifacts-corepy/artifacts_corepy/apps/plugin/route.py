# coding=utf-8

from __future__ import absolute_import

from artifacts_corepy.apps.plugin import controller


def add_routes(api):
    # plugin create image package
    api.add_route('/artifacts/v1/packages/from-image', controller.PackageFromImage())

    # plugin upload to nexus from remote nexus
    api.add_route('/artifacts/v1/packages/from-remote', controller.PackageFromRemote())
