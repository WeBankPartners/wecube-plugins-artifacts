# coding=utf-8

from __future__ import absolute_import


class PackageType(object):
    app = 'APP'
    db = 'DB'
    mixed = 'APP&DB'
    image = 'IMAGE'
    default = 'APP&DB'


class CompareResult(object):
    same = 'same'
    new = 'new'
    changed = 'changed'
    deleted = 'deleted'
