# -*- coding: utf-8 -*-
from __future__ import absolute_import

from artifacts_corepy.common.mixin import CollectionController, ItemController
from artifacts_corepy.apps.variable import api


class CollectionDiffConfTemplates(CollectionController):
    name = 'artifacts.diff-conf-templates'
    resource = api.DiffConfTemplate


class ItemDiffConfTemplate(ItemController):
    name = 'artifacts.diff-conf-templates'
    resource = api.DiffConfTemplate
