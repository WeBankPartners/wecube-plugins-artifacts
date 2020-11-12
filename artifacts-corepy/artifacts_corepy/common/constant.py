# coding=utf-8

from __future__ import absolute_import


class PackageType(object):
    app = 'app'
    db = 'db'
    mixed = 'mixed'


class CompareResult(object):
    same = 'same'
    new = 'new'
    changed = 'changed'
    deleted = 'deleted'
