# coding=utf-8

from __future__ import absolute_import

import falcon
from talos.common.controller import CollectionController
from talos.common.controller import ItemController
from talos.core import exceptions
from talos.core import utils
from talos.core.i18n import _

from artifacts_corepy.common import exceptions as my_exceptions


class Collection(CollectionController):
    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        resp.json = {'code': 200, 'status': 'OK', 'data': self.list(req, None, **kwargs), 'message': 'success'}

    def list(self, req, criteria, **kwargs):
        return self.make_resource(req).list(req.params, **kwargs)


class Item(ItemController):
    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        resp.json = {'code': 200, 'status': 'OK', 'data': self.get(req, **kwargs), 'message': 'success'}

    def get(self, req, **kwargs):
        return self.make_resource(req).get(**kwargs)

    def on_post(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        data = req.json
        resp.json = {'code': 200, 'status': 'OK', 'data': self.update(req, data, **kwargs), 'message': 'success'}

    def update(self, req, data, **kwargs):
        return self.make_resource(req).update(data, **kwargs)


class POSTCollection(CollectionController):
    def on_post(self, req, resp, **kwargs):
        self._validate_method(req)
        resp.json = {'code': 200, 'status': 'OK', 'data': self.list(req, None, **kwargs), 'message': 'success'}

    def list(self, req, criteria, **kwargs):
        return self.make_resource(req).list_by_post(req.json, **kwargs)