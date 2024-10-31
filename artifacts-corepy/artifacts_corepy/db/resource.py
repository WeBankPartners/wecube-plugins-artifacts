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
        resource['create_user'] = scoped_globals.GLOBALS.request.auth_user or None

    def _before_update(self, rid, resource, validate):
        resource['update_user'] = scoped_globals.GLOBALS.request.auth_user or None


class DiffConfTemplate(MetaCRUD):
    orm_meta = models.DiffConfTemplate
    _default_order = ['-id', 'update_time', 'create_time']

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
        # crud.ColumnValidator(field='updated_user', validate_on=('*:O',), nullable=True),
        # crud.ColumnValidator(field='updated_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='roles',
                             rule=validator.TypeValidator(list),
                             validate_on=('create:M', 'update:O'),
                             orm_required=False),
    ]


class DiffConfTemplateRole(crud.ResourceBase):
    orm_meta = models.DiffConfTemplateRole
    _default_order = ['-id']

