# coding=utf-8

from __future__ import absolute_import

import cgi
from talos.core import config
from talos.core.i18n import _
from talos.core import exceptions as core_ex
from talos.common import controller as base_controller

from artifacts_corepy.common.controller import Collection, Item, POSTCollection
from artifacts_corepy.apps.package import api as package_api

CONF = config.CONF


class ControllerDeployPackageCiTypeId(object):
    def on_get(self, req, resp, **kwargs):
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': int(CONF.wecube.wecmdb.citypes.deploy_package),
            'message': 'success'
        }


class CollectionSystemDesign(Collection):
    allow_methods = ('GET', )
    name = 'artifacts.system-designs'
    resource = package_api.SystemDesign


class ItemSystemDesign(Item):
    allow_methods = ('GET', )
    name = 'artifacts.system-design.item'
    resource = package_api.SystemDesign


class CollectionSpecialConnector(Collection):
    allow_methods = ('GET', )
    name = 'artifacts.special-connector'
    resource = package_api.SpecialConnector


class CollectionCiTypes(Collection):
    allow_methods = ('GET', )
    name = 'artifacts.ci-types'
    resource = package_api.CiTypes


class CollectionEnumCodes(POSTCollection):
    allow_methods = ('POST', )
    name = 'artifacts.enum-codes'
    resource = package_api.EnumCodes


class CollectionUnitDesignPackages(POSTCollection):
    allow_methods = ('POST', )
    name = 'artifacts.unit-design.packages'
    resource = package_api.UnitDesignPackages


class CollectionUnitDesignNexusPackages(Collection):
    allow_methods = ('GET', )
    name = 'artifacts.unit-design.nexus.packages'
    resource = package_api.UnitDesignNexusPackages


class CollectionUnitDesignNexusPackageUpload(object):
    name = 'artifacts.unit-design.nexus.package.upload'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        download_url = req.params.get('downloadUrl', None)
        if not download_url:
            raise core_ex.ValidationError(message=_('missing query: downloadUrl'))
        form = cgi.FieldStorage(fp=req.stream, environ=req.env)
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.upload(req, download_url, **kwargs),
            'message': 'success'
        }

    def upload(self, req, download_url, **kwargs):
        return self.resource().upload_from_nexus(download_url, **kwargs)


class CollectionUnitDesignPackageUpload(object):
    name = 'artifacts.unit-design.package.upload'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        form = cgi.FieldStorage(fp=req.stream, environ=req.env)
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.upload(req, form['file'].filename, form['file'].type, form['file'].file, **kwargs),
            'message': 'success'
        }

    def upload(self, req, filename, filetype, fileobj, **kwargs):
        return self.resource().upload(filename, filetype, fileobj, **kwargs)


class ItemPackage(Item):
    allow_methods = ('GET', )
    name = 'artifacts.deploy-package.item'
    resource = package_api.UnitDesignPackages


class UnitDesignPackageBaselineCompare(base_controller.Controller):
    name = 'artifacts.deploy-package.baseline.compare'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        self._validate_data(req)
        data = req.json
        if 'baselinePackage' not in data:
            raise core_ex.FieldRequired(attribute='baselinePackage')
        kwargs['baseline_package_id'] = data['baselinePackage']
        resp.json = {'code': 200, 'status': 'OK', 'data': self.baseline_compare(req, **kwargs), 'message': 'success'}

    def baseline_compare(self, req, **kwargs):
        return self.resource().baseline_compare(**kwargs)


class UnitDesignPackageFileTree(base_controller.Controller):
    name = 'artifacts.deploy-package.filetree'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        self._validate_data(req)
        data = req.json
        if 'fileList' not in data:
            raise core_ex.FieldRequired(attribute='fileList')
        kwargs['baseline_package_id'] = data.get('baselinePackage', None)
        kwargs['expand_all'] = data.get('expandAll', False)
        kwargs['files'] = data['fileList']
        resp.json = {'code': 200, 'status': 'OK', 'data': self.filetree(req, **kwargs), 'message': 'success'}

    def filetree(self, req, **kwargs):
        return self.resource().filetree(**kwargs)