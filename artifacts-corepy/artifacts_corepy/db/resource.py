# -*- coding: utf-8 -*-

from __future__ import absolute_import

from talos.core import utils
from talos.db import crud, validator
from talos.utils import scoped_globals

from artifacts_corepy.db import validator as my_validator
from artifacts_corepy.db import models
from artifacts_corepy.common import exceptions


class MetaCRUD(crud.ResourceBase):
    _id_prefix = ''
    _remove_fields = []

    def _before_create(self, resource, validate):
        if 'id' not in resource and self._id_prefix:
            resource['id'] = utils.generate_prefix_uuid(self._id_prefix)
        resource['create_user'] = scoped_globals.GLOBALS.request.auth_user or None

    def _before_update(self, rid, resource, validate):
        resource['update_user'] = scoped_globals.GLOBALS.request.auth_user or None

    def _apply_primary_key_filter(self, query, rid):
        query = super()._apply_primary_key_filter(query, rid)

        if hasattr(self.orm_meta, 'is_deleted'):
            query = query.filter(self.orm_meta.is_deleted == 0)

        return query

    def _addtional_list(self, query, filters):
        query = super()._addtional_list(query, filters)
        if hasattr(self.orm_meta, 'is_deleted'):
            query = query.filter(self.orm_meta.is_deleted == 0)
        return query


class DiffConfTemplate(MetaCRUD):
    orm_meta = models.DiffConfTemplate
    _default_order = ['-id', 'update_time', 'create_time']

    _validate = [
        crud.ColumnValidator(field='type',
                             # rule=my_validator.validator.InValidator(['app', 'db']),
                             rule=my_validator.LengthValidator(0, 16),
                             validate_on=('create:O', 'update:O')),
        crud.ColumnValidator(field='code',
                             rule=my_validator.LengthValidator(1, 36),
                             validate_on=('create:M', 'update:M'),
                             # error_msg='%(result)s exist error, please check',
                             nullable=False),
        crud.ColumnValidator(field='value',
                             rule=my_validator.LengthValidator(1, 40960),
                             validate_on=('create:M', 'update:M')),
        crud.ColumnValidator(field='description',
                             rule=my_validator.LengthValidator(0, 128),
                             validate_on=('*:O',),
                             nullable=True),
        crud.ColumnValidator(field='create_user', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='update_user', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='roles',
                             rule=validator.TypeValidator(dict),
                             validate_on=('create:M', 'update:O'),
                             orm_required=False),
    ]

    def _before_create(self, resource, validate):
        if 'id' not in resource and self._id_prefix:
            resource['id'] = utils.generate_prefix_uuid(self._id_prefix)
        resource['create_user'] = scoped_globals.GLOBALS.request.auth_user or None

        # 单独校验 code，返回人性化报错信息
        if self.list({'code': resource['code']}):
            raise exceptions.ValidationError('code: %s exist error, please check' % resource['code'])

class DiffConfTemplateRole(crud.ResourceBase):
    orm_meta = models.DiffConfTemplateRole
    _default_order = ['-id']


class SysRoleMenu(MetaCRUD):
    orm_meta = models.SysRoleMenu
    _default_order = ['-created_time']


class SysRoleUser(MetaCRUD):
    orm_meta = models.SysRoleUser
    _default_order = ['-created_time']


class SysMenu(MetaCRUD):
    orm_meta = models.SysMenu
    _default_order = ['seq_no']
    _id_prefix = 'menu-'

    _validate = [
        crud.ColumnValidator(field='id', validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='display_name',
                             rule=my_validator.LengthValidator(1, 64),
                             validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='url',
                             rule=my_validator.LengthValidator(0, 255),
                             validate_on=('create:O', 'update:O'),
                             nullable=True),
        crud.ColumnValidator(field='seq_no',
                             rule=my_validator.validator.NumberValidator(int, range_min=0, range_max=65535),
                             validate_on=('create:O', 'update:O')),
        crud.ColumnValidator(field='parent',
                             rule=my_validator.BackRefValidator(SysRoleMenu),
                             validate_on=('create:O', 'update:O'),
                             nullable=True),
        crud.ColumnValidator(field='is_active',
                             rule=my_validator.validator.InValidator(['yes', 'no']),
                             validate_on=('create:O', 'update:O')),
        crud.ColumnValidator(field='created_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='created_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_time', validate_on=('*:O',), nullable=True),
    ]


class SysRole(MetaCRUD):
    orm_meta = models.SysRole
    _default_order = ['-created_time']
    _id_prefix = 'role-'
    _detail_relationship_as_summary = True

    _validate = [
        crud.ColumnValidator(field='id', validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='description',
                             rule=my_validator.LengthValidator(1, 255),
                             validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='role_type',
                             rule=my_validator.LengthValidator(0, 32),
                             validate_on=('create:O', 'update:O'),
                             nullable=True),
        crud.ColumnValidator(field='is_system',
                             rule=my_validator.validator.InValidator(['yes', 'no']),
                             validate_on=('create:O', 'update:O')),
        crud.ColumnValidator(field='created_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='created_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_time', validate_on=('*:O',), nullable=True),
    ]


class SysUser(MetaCRUD):
    orm_meta = models.SysUser
    _default_order = ['-created_time']
    _remove_fields = ['password', 'salt']
    _id_prefix = 'user-'

    _validate = [
        crud.ColumnValidator(field='id', validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='display_name',
                             rule=my_validator.LengthValidator(1, 64),
                             validate_on=('create:M', 'update:O')),
        crud.ColumnValidator(field='password', rule=my_validator.LengthValidator(1, 128), validate_on=('create:M',)),
        crud.ColumnValidator(field='salt', rule=my_validator.LengthValidator(1, 36), validate_on=('create:M',)),
        crud.ColumnValidator(field='description',
                             rule=my_validator.LengthValidator(0, 255),
                             validate_on=('create:O', 'update:O'),
                             nullable=True),
        crud.ColumnValidator(field='is_system',
                             rule=my_validator.validator.InValidator(['yes', 'no']),
                             validate_on=('create:O', 'update:O')),
        crud.ColumnValidator(field='created_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='created_time', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_by', validate_on=('*:O',), nullable=True),
        crud.ColumnValidator(field='updated_time', validate_on=('*:O',), nullable=True),
    ]

    def list_internal(self, filters=None, orders=None, offset=None, limit=None, hooks=None):
        return super(MetaCRUD, self).list(filters=filters, orders=orders, offset=offset, limit=limit, hooks=hooks)
