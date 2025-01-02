# -*- coding: utf-8 -*-

from __future__ import absolute_import

import falcon
from talos.common.controller import CollectionController as BaseCollectionController
from talos.common.controller import ItemController as BaseItemController
from talos.common.controller import Controller as BaseController
from talos.core import exceptions as base_ex
from talos.core import utils
from talos.core.i18n import _

from artifacts_corepy.common import exceptions


class Controller(BaseController):
    allow_methods = (
        'GET',
        'POST',
    )

    def on_post(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        data = req.json
        resp.json = {'code': 200, 'status': 'OK', 'data': self.create(req, data, **kwargs), 'message': 'success'}
        resp.status = falcon.HTTP_200

    def create(self, req, data, **kwargs):
        return self.make_resource(req).create(data, **kwargs)

    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        resp.json = {'code': 200, 'status': 'OK', 'data': self.get(req, **kwargs), 'message': 'success'}
        resp.status = falcon.HTTP_200

    def get(self, req, **kwargs):
        return self.make_resource(req).get(**kwargs)


class CollectionController(BaseCollectionController):
    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        refs = []
        count = 0
        criteria = self._build_criteria(req)
        if criteria:
            refs = self.list(req, criteria, **kwargs)
            count = self.count(req, criteria, results=refs, **kwargs)
        resp.json = {'code': 200, 'status': 'OK', 'data': {'count': count, 'data': refs}, 'message': 'success'}

    def on_post(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        datas = req.json
        if not utils.is_list_type(datas):
            raise exceptions.PluginError(_('data must be list type'))
        rets = []
        ex_rets = []
        for idx, data in enumerate(datas):
            try:
                rets.append(self.create(req, data, **kwargs))
            except base_ex.Error as e:
                # 添加 errorMessage，使其匹配前端错误解析协议
                ex_rets.append({'index': idx + 1, 'message': str(e), 'errorMessage': str(e)})
        if len(ex_rets):
            raise exceptions.BatchPartialError(num=len(ex_rets), action='create', exception_data={'data': ex_rets})
        resp.json = {'code': 200, 'status': 'OK', 'data': rets, 'message': 'success'}
        resp.status = falcon.HTTP_200

    def on_patch(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        datas = req.json
        if not utils.is_list_type(datas):
            raise exceptions.PluginError(_('data must be list type'))
        rets = []
        ex_rets = []
        for idx, data in enumerate(datas):
            try:
                res_instance = self.make_resource(req)
                if res_instance.primary_keys not in data:
                    raise exceptions.FieldRequired(attribute=res_instance.primary_keys)
                rid = data.pop(res_instance.primary_keys)
                before_update, after_update = self.update(req, data, rid=rid)
                if after_update is None:
                    raise exceptions.NotFoundError(resource='%s[%s]' % (self.resource.__name__, rid))
                rets.append(after_update)
            except base_ex.Error as e:
                ex_rets.append({'index': idx + 1, 'message': str(e)})
        if len(ex_rets):
            raise exceptions.BatchPartialError(num=len(ex_rets), action='update', exception_data={'data': ex_rets})
        resp.json = {'code': 200, 'status': 'OK', 'data': rets, 'message': 'success'}
        resp.status = falcon.HTTP_200

    def update(self, req, data, **kwargs):
        rid = kwargs.pop('rid')
        return self.make_resource(req).update(rid, data)

    def on_delete(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        datas = req.json
        if not utils.is_list_type(datas):
            raise exceptions.PluginError(_('data must be list type'))
        rets = []
        ex_rets = []
        for idx, data in enumerate(datas):
            try:
                res_instance = self.make_resource(req)
                ref_count, ref_details = self.delete(req, rid=data)
                rets.append(ref_details[0])
            except base_ex.Error as e:
                ex_rets.append({'index': idx + 1, 'message': str(e)})
        if len(ex_rets):
            raise exceptions.BatchPartialError(num=len(ex_rets), action='delete', exception_data={'data': ex_rets})
        resp.json = {'code': 200, 'status': 'OK', 'data': rets, 'message': 'success'}
        resp.status = falcon.HTTP_200

    def delete(self, req, **kwargs):
        # before, after = self.make_resource(req).update(
        #     rid=kwargs.get('rid'), resource={"is_deleted": 1}, validate=False
        # )
        # return 1 if before else 0, [after]
        return self.make_resource(req).delete(**kwargs)


class ItemController(BaseItemController):

    def on_get(self, req, resp, **kwargs):
        self._validate_method(req)
        ref = self.get(req, **kwargs)
        if ref is not None:
            resp.json = {'code': 200, 'status': 'OK', 'data': ref, 'message': 'success'}
        else:
            raise exceptions.NotFoundError(resource='%s[%s]' % (self.resource.__name__, kwargs.get('rid', '-')))

    def on_patch(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        data = req.json
        if data is not None and not isinstance(data, dict):
            raise exceptions.PluginError(_('data must be dict type'))
        ref_before, ref_after = self.update(req, data, **kwargs)
        if ref_after is not None:
            resp.json = {'code': 200, 'status': 'OK', 'data': ref_after, 'message': 'success'}
        else:
            raise exceptions.NotFoundError(resource='%s[%s]' % (self.resource.__name__, kwargs.get('rid', '-')))

    def on_delete(self, req, resp, **kwargs):
        self._validate_method(req)
        ref, details = self.delete(req, **kwargs)
        if ref:
            resp.json = {'code': 200, 'status': 'OK', 'data': {'count': ref, 'data': details}, 'message': 'success'}
        else:
            raise exceptions.NotFoundError(resource='%s[%s]' % (self.resource.__name__, kwargs.get('rid', '-')))

    # def delete(self, req, **kwargs):
    #     before, after = self.make_resource(req).update(
    #         rid=kwargs.get('rid'), resource={"is_deleted": 1}, validate=False
    #     )
    #     return 1 if before else 0, [after]
