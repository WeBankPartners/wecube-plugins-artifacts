# -*- coding: utf-8 -*-

from __future__ import absolute_import

from talos.core import config
from artifacts_corepy.apps.variable import controller

CONF = config.CONF


def add_routes(api):
    api.add_route('/artifacts/api/v1/diff-conf-templates', controller.CollectionDiffConfTemplates())
    api.add_route('/artifacts/api/v1/diff-conf-templates/{rid}', controller.ItemDiffConfTemplate())
