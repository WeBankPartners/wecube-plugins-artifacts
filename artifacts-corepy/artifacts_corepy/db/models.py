# -*- coding: utf-8 -*-
from __future__ import absolute_import

from talos.db.dictbase import DictBase
from sqlalchemy import (
    Column, DateTime, ForeignKey, String, text, Text, func, create_engine, UniqueConstraint,
)
from sqlalchemy.dialects.mysql import BIGINT, TINYINT, INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DiffConfTemplate(Base, DictBase):
    __tablename__ = 'diff_conf_template'

    attributes = [
        'id', 'type', 'code', 'value', 'description', 'create_user', 'create_time', 'update_user', 'update_time',
        'roles',
    ]

    id = Column(BIGINT, primary_key=True, index=True)
    type = Column(String(16), nullable=True, comment='类型：应用-app,数据库-db')
    code = Column(String(36), nullable=False, unique=True, comment='编码')
    value = Column(Text, comment='文本值')
    description = Column(String(128), server_default=text("''"))
    create_user = Column(String(36))
    create_time = Column(DateTime, default=func.now())
    update_user = Column(String(36))
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    # is_deleted = Column(TINYINT, nullable=False, default=0, comment='软删除:0,1')

    roles = relationship("DiffConfTemplateRole", back_populates="diff_conf_template")

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "{0}:{1}".format(self.type, self.code)
    
# ... existing code ...

class PrivateVariableTemplate(Base, DictBase):
    __tablename__ = 'private_variable_template'
    
    attributes = [
        'id', 'name', 'diff_conf_template_id', 'description', 'create_user', 'create_time', 'update_user', 'update_time',
        'diff_conf_template'
    ]
    
    id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String(36), nullable=False, comment='私有变量名称')
    diff_conf_template_id = Column(ForeignKey('diff_conf_template.id'), nullable=False, comment='关联的差异化配置模板ID')
    description = Column(String(128), server_default=text("''"), comment='描述')
    create_user = Column(String(36))
    create_time = Column(DateTime, default=func.now())
    update_user = Column(String(36))
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联到 DiffConfTemplate
    diff_conf_template = relationship("DiffConfTemplate", backref="private_variable_templates")
    
    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return "{0}:{1}".format(self.name, self.diff_conf_template_id)


class DiffConfTemplateRole(Base, DictBase):
    __tablename__ = 'diff_conf_template_role'
    attributes = ['role', 'permission']

    id = Column(BIGINT, primary_key=True, nullable=False)
    permission = Column(String(16), nullable=False, comment='权限：MGMT,USE')
    role = Column(String(64), nullable=False, comment='角色')

    diff_conf_template_id = Column(ForeignKey('diff_conf_template.id', ondelete='CASCADE'))
    diff_conf_template = relationship('DiffConfTemplate', lazy=True)

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "{0}:{1}".format(self.role, self.diff_conf_template_id)


class SysMenu(Base, DictBase):
    __tablename__ = 'sys_menu'
    attributes = [
        'id', 'display_name', 'url', 'seq_no', 'parent', 'is_active', 'created_by', 'created_time', 'updated_by',
        'updated_time'
    ]
    summary_attributes = ['id', 'display_name', 'url', 'seq_no', 'parent', 'is_active']

    id = Column(String(36), primary_key=True, comment='主键')
    display_name = Column(String(64), comment='显示名')
    url = Column(String(255), comment='访问路径')
    seq_no = Column(INTEGER(11), server_default=text("'0'"), comment='排序号')
    parent = Column(String(36), comment='父菜单')
    is_active = Column(String(8), server_default=text("'yes'"), comment='状态')
    created_by = Column(String(36))
    created_time = Column(DateTime)
    updated_by = Column(String(36))
    updated_time = Column(DateTime)

    roles = relationship("SysRole", secondary="sys_role_menu", back_populates="menus", uselist=True, viewonly=True)


class SysRole(Base, DictBase):
    __tablename__ = 'sys_role'
    attributes = [
        'id', 'description', 'role_type', 'is_system', 'created_by', 'created_time', 'updated_by', 'updated_time',
        'menus'
    ]
    summary_attributes = ['id', 'description', 'role_type', 'is_system']
    detail_attributes = [
        'id', 'description', 'role_type', 'is_system', 'created_by', 'created_time', 'updated_by', 'updated_time',
        'users', 'menus'
    ]

    id = Column(String(36), primary_key=True, comment='主键')
    description = Column(String(255), comment='描述')
    role_type = Column(String(32), comment='角色类型')
    is_system = Column(String(8), server_default=text("'no'"), comment='是否系统角色')
    created_by = Column(String(36))
    created_time = Column(DateTime)
    updated_by = Column(String(36))
    updated_time = Column(DateTime)

    users = relationship("SysUser", secondary="sys_role_user", back_populates="roles", uselist=True, viewonly=True)
    menus = relationship("SysMenu", secondary="sys_role_menu", back_populates="roles", uselist=True, viewonly=True)


class SysUser(Base, DictBase):
    __tablename__ = 'sys_user'
    attributes = [
        'id', 'display_name', 'password', 'salt', 'description', 'is_system', 'created_by', 'created_time',
        'updated_by', 'updated_time'
    ]
    summary_attributes = ['id', 'display_name', 'description', 'is_system']
    detail_attributes = [
        'id', 'display_name', 'password', 'salt', 'description', 'is_system', 'created_by', 'created_time',
        'updated_by', 'updated_time', 'roles'
    ]

    id = Column(String(36), primary_key=True, comment='主键')
    display_name = Column(String(64), comment='显示名')
    password = Column(String(128), comment='加密密钥')
    salt = Column(String(36), comment='加密盐')
    description = Column(String(255), comment='描述')
    is_system = Column(String(8), server_default=text("'no'"), comment='是否系统用户')
    created_by = Column(String(36))
    created_time = Column(DateTime)
    updated_by = Column(String(36))
    updated_time = Column(DateTime)

    roles = relationship("SysRole", secondary="sys_role_user", back_populates="users", uselist=True, viewonly=True)


class SysRoleMenu(Base, DictBase):
    __tablename__ = 'sys_role_menu'

    id = Column(BIGINT(20), primary_key=True)
    role_id = Column(ForeignKey('sys_role.id'), index=True, comment='角色id')
    menu_id = Column(ForeignKey('sys_menu.id'), index=True, comment='菜单id')
    created_by = Column(String(36))
    created_time = Column(DateTime)
    updated_by = Column(String(36))
    updated_time = Column(DateTime)

    menu = relationship('SysMenu')
    role = relationship('SysRole')


class SysRoleUser(Base, DictBase):
    __tablename__ = 'sys_role_user'

    id = Column(BIGINT(20), primary_key=True)
    role_id = Column(ForeignKey('sys_role.id'), index=True, comment='角色id')
    user_id = Column(ForeignKey('sys_user.id'), index=True, comment='用户id')
    created_by = Column(String(36))
    created_time = Column(DateTime)
    updated_by = Column(String(36))
    updated_time = Column(DateTime)

    role = relationship('SysRole')
    user = relationship('SysUser')
