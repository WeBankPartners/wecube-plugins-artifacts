# -*- coding: utf-8 -*-
from __future__ import absolute_import

from talos.db.dictbase import DictBase
from sqlalchemy import Column, DateTime, ForeignKey, String, text, Text, func, create_engine
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DiffConfTemplate(Base, DictBase):
    __tablename__ = 'diff_conf_template'
    attributes = [
        'id', 'type', 'code', 'value', 'description', 'create_user', 'create_time', 'update_user', 'update_time',
        'is_deleted', 'roles',
    ]

    id = Column(BIGINT, primary_key=True, index=True)
    type = Column(String(16), nullable=False, comment='类型：应用-app,数据库-db')
    code = Column(String(36), nullable=False, comment='编码')
    value = Column(Text, comment='文本值')
    description = Column(String(128), server_default=text("''"))
    create_user = Column(String(36))
    create_time = Column(DateTime, default=func.now())
    update_user = Column(String(36))
    update_time = Column(DateTime, onupdate=func.now())
    is_deleted = Column(TINYINT, nullable=False, default=0, comment='软删除:0,1')

    roles = relationship("DiffConfTemplateRole", back_populates="diff_conf_template")

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "{0}:{1}".format(self.type, self.code)


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


if __name__ == '__main__':
    engine = create_engine("mysql+pymysql://root:miya.12345@127.0.0.1:3306/artifacts", encoding="utf-8")
    Base.metadata.create_all(engine)
