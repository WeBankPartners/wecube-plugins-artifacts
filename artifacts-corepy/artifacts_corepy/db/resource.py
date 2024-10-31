# -*- coding: utf-8 -*-

from __future__ import absolute_import

from talos.core import utils
from talos.db import crud, validator
from talos.utils import scoped_globals

from artifacts_corepy.db import validator as my_validator
from artifacts_corepy.db import models


class MetaCRUD(crud.ResourceBase):
    _id_prefix = ''
    _remove_fields = []

    def _before_create(self, resource, validate):
        if 'id' not in resource and self._id_prefix:
            resource['id'] = utils.generate_prefix_uuid(self._id_prefix)
        resource['created_user'] = scoped_globals.GLOBALS.request.auth_user or None

    def _before_update(self, rid, resource, validate):
        resource['updated_user'] = scoped_globals.GLOBALS.request.auth_user or None

    def create(self, resource, validate=True, detail=True):
        ref = super().create(resource, validate=validate, detail=detail)
        if ref and self._remove_fields:
            for field in self._remove_fields:
                del ref[field]
        return ref

    def list(self, filters=None, orders=None, offset=None, limit=None, hooks=None):
        refs = super().list(filters=filters, orders=orders, offset=offset, limit=limit, hooks=hooks)
        if self._remove_fields:
            for ref in refs:
                for field in self._remove_fields:
                    del ref[field]
        return refs

    def get(self, rid):
        ref = super().get(rid)
        if ref and self._remove_fields:
            for field in self._remove_fields:
                del ref[field]
        return ref

    def update(self, rid, resource, filters=None, validate=True, detail=True):
        before_update, after_update = super().update(rid, resource, filters=filters, validate=validate, detail=detail)
        if before_update and self._remove_fields:
            for field in self._remove_fields:
                del before_update[field]
        if after_update and self._remove_fields:
            for field in self._remove_fields:
                del after_update[field]
        return (before_update, after_update)

    def delete(self, rid, filters=None, detail=True):
        num_ref, refs = super().delete(rid, filters=filters, detail=detail)
        for ref in refs:
            if self._remove_fields:
                for field in self._remove_fields:
                    del ref[field]
        return (num_ref, refs)

    def delete_all(self, filters=None):
        num_ref, refs = super().delete_all(filters=filters)
        for ref in refs:
            if self._remove_fields:
                for field in self._remove_fields:
                    del ref[field]
        return (num_ref, refs)


class DiffConfTemplate(MetaCRUD):
    orm_meta = models.DiffConfTemplate
    _default_order = ['-id']

    _validate = [
        crud.ColumnValidator(field='type',
                             rule=my_validator.LengthValidator(1, 16),
                             validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='code',
                             rule=my_validator.LengthValidator(1, 36),
                             validate_on=('create:M', 'update:M'),
                             nullable=False),
        crud.ColumnValidator(field='value',
                             rule=my_validator.LengthValidator(1, 40960),
                             validate_on=('create:M', 'update:M')),
        crud.ColumnValidator(field='description',
                             rule=my_validator.LengthValidator(0, 128),
                             validate_on=('create:O', 'update:O'),
                             nullable=True),
        crud.ColumnValidator(field='created_user', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='created_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_user', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='roles',
                             rule=validator.TypeValidator(dict),
                             validate_on=('create:M', 'update:O'),
                             orm_required=False),
    ]


class RoleDiffConfTemplate(crud.ResourceBase):
    orm_meta = models.DiffConfTemplateRole
    _default_order = ['-id']

