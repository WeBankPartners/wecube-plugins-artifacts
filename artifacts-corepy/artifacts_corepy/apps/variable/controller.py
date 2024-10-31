# -*- coding: utf-8 -*-
from __future__ import absolute_import

from artifacts_corepy.common import exceptions
from artifacts_corepy.common.model_controller import Collection, Item
from artifacts_corepy.apps.variable import api


class CollectionDiffConfTemplates(Collection):
    name = 'artifacts.diff_conf_templates'
    resource = api.DiffConfTemplate

    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        refs = []
        count = 0
        criteria = self._build_criteria(req)
        if criteria:
            refs = self.list_query(req, criteria, **kwargs)
            for r in refs:
                # remove password info
                r.pop('password', None)
            count = len(refs)
        resp.json = {'code': 200, 'status': 'OK', 'data': {'count': count, 'data': refs}, 'message': 'success'}

    def list_query(self, req, criteria, **kwargs):
        criteria.pop('fields', None)
        refs = self.make_resource(req).list_query(**criteria)
        return refs


class ItemDiffConfTemplate(Item):
    name = 'artifacts.diff_conf_templates'
    resource = api.DiffConfTemplate
