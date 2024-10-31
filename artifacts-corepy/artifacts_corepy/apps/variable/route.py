# -*- coding: utf-8 -*-

from __future__ import absolute_import

from artifacts_corepy.apps.variable import controller


def add_routes(api):
    api.add_route('/artifacts/v1/diff-conf-templates', controller.CollectionDiffConfTemplates())
    api.add_route('/artifacts/v1/diff-conf-templates/{rid}', controller.ItemDiffConfTemplate())
