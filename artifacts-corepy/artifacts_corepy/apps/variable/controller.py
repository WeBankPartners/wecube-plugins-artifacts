# -*- coding: utf-8 -*-
from __future__ import absolute_import

from artifacts_corepy.common.mixin import CollectionController, ItemController
from artifacts_corepy.apps.variable import api


class CollectionDiffConfTemplates(CollectionController):
    name = 'artifacts.diff_conf_templates'
    resource = api.DiffConfTemplate


class ItemDiffConfTemplate(ItemController):
    name = 'artifacts.diff_conf_template'
    resource = api.DiffConfTemplate
