# coding=utf-8

from __future__ import absolute_import

import cgi
import falcon
import os
import urllib.parse
from talos.core import utils
from talos.core import config
from talos.core.i18n import _
from talos.common import controller as base_controller

from artifacts_corepy.common.controller import Collection, Item, POSTCollection
from artifacts_corepy.common import exceptions
from artifacts_corepy.apps.package import apiv2 as package_api

CONF = config.CONF


class ControllerDeployPackageCiTypeId(object):
    name = 'artifacts.deploy-package.citypeid'

    def on_get(self, req, resp, **kwargs):
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': CONF.wecube.wecmdb.citypes.deploy_package,
            'message': 'success'
        }


class ControllerVariableRootCiTypeId(object):
    name = 'artifacts.deploy-package.varrootcitypeid'

    def on_get(self, req, resp, **kwargs):
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': {
                'app': CONF.wecube.wecmdb.citypes.app_root_ci,
                'db': CONF.wecube.wecmdb.citypes.db_root_ci,
                'app_template': CONF.wecube.wecmdb.citypes.app_template_ci,
                'db_template': CONF.wecube.wecmdb.citypes.db_template_ci
            },
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


class ItemEnumCodes(Item):
    allow_methods = ('GET', )
    name = 'artifacts.enum-codes'
    resource = package_api.EnumCodes


class ItemCITypeOperations(Item):
    allow_methods = ('GET', )
    name = 'artifacts.ci-operations'
    resource = package_api.CITypeOperations


class CollectionUnitDesignPackages(POSTCollection):
    allow_methods = ('POST', )
    name = 'artifacts.unit-design.packages'
    resource = package_api.UnitDesignPackages


class CollectionUnitDesignNexusPackages(POSTCollection):
    allow_methods = ('POST', )
    name = 'artifacts.unit-design.nexus.packages'
    resource = package_api.UnitDesignNexusPackages
    
class ItemUnitDesignNexusPackages(Item):
    allow_methods = ('GET', )
    name = 'artifacts.unit-design.nexus.path'
    resource = package_api.UnitDesignNexusPackages


class CollectionUnitDesignNexusPackageUpload(object):
    name = 'artifacts.unit-design.nexus.package.upload'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        download_url = req.params.get('downloadUrl', None)
        baseline_package = req.params.get('baseline_package', None)
        if not download_url:
            raise exceptions.ValidationError(message=_('missing query: downloadUrl'))
        form = cgi.FieldStorage(fp=req.stream, environ=req.env)
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.upload(req, download_url, baseline_package, **kwargs),
            'message': 'success'
        }

    def upload(self, req, download_url, baseline_package, **kwargs):
        return self.resource().upload_from_nexus(download_url, baseline_package, **kwargs)


class CollectionUnitDesignPackageUpload(object):
    name = 'artifacts.unit-design.package.upload'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        form = cgi.FieldStorage(fp=req.stream, environ=req.env)
        baseline_package = None
        if 'baseline_package' in form:
            baseline_package = form.getvalue('baseline_package', None)
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.upload(req, form['file'].filename, form['file'].type, form['file'].file, baseline_package, **kwargs),
            'message': 'success'
        }

    def upload(self, req, filename, filetype, fileobj, baseline_package, **kwargs):
        return self.resource().upload(filename, filetype, fileobj, baseline_package, **kwargs)


class ItemPackage(Item):
    allow_methods = ('GET', )
    name = 'artifacts.deploy-package.item'
    resource = package_api.UnitDesignPackages


class ItemPackageHistory(Item):
    allow_methods = ('GET', )
    name = 'artifacts.deploy-package.itemhistory'
    resource = package_api.PackageHistory


class ItemPackageUpdate(Item):
    allow_methods = ('POST', )
    name = 'artifacts.deploy-package.item.update'
    resource = package_api.UnitDesignPackages


class UnitDesignPackageBaselineCompare(base_controller.Controller):
    name = 'artifacts.deploy-package.baseline.compare'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        self._validate_data(req)
        data = req.json
        if 'baselinePackage' not in data:
            raise exceptions.FieldRequired(attribute='baselinePackage')
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
            raise exceptions.FieldRequired(attribute='fileList')
        kwargs['baseline_package_id'] = data.get('baselinePackage', None)
        kwargs['expand_all'] = data.get('expandAll', False)
        kwargs['files'] = data['fileList']
        resp.json = {'code': 200, 'status': 'OK', 'data': self.filetree(req, **kwargs), 'message': 'success'}

    def filetree(self, req, **kwargs):
        return self.resource().filetree(**kwargs)


class ItemDiffConfigUpdate(Item):
    allow_methods = ('POST', )
    name = 'artifacts.diff-config.update'
    resource = package_api.DiffConfig


class UnitDesignPackageBaselineFilesCompare(base_controller.Controller):
    name = 'artifacts.deploy-package.baseline.files.compare'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        self._validate_data(req)
        data = req.json or {}
        kwargs['baseline_package_id'] = data.pop('baselinePackage', None)
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.baseline_files_compare(req, data, **kwargs),
            'message': 'success'
        }

    def baseline_files_compare(self, req, data, **kwargs):
        return self.resource().baseline_files_compare(data, **kwargs)


class ItemUploadAndCreatePackage(base_controller.Controller):
    name = 'artifacts.deploy-package.upload_and_create'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        self._validate_data(req)
        data = req.json or {}
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.upload_and_create(req, data, **kwargs),
            'message': 'success'
        }

    def upload_and_create(self, req, data, **kwargs):
        return self.resource().upload_and_create(data, **kwargs)


class ItemCiReferences(Item):
    allow_methods = ('GET', )
    name = 'artifacts.cireferences'
    resource = package_api.CiTypes

    def get(self, req, **kwargs):
        return self.make_resource(req).get_references(**kwargs)


class ItemCiAttributes(Item):
    allow_methods = ('GET', )
    name = 'artifacts.ciattributes'
    resource = package_api.CiTypes

    def get(self, req, **kwargs):
        accept_types = req.params.get('accept-input-types', None)
        accept_types = accept_types.split(',') if accept_types else None
        return self.make_resource(req).get_attributes(accept_types, **kwargs)


class CiStateAction(Item):
    allow_methods = ('POST', )
    name = 'artifacts.cistate.action'
    resource = package_api.CiTypes

    def update(self, req, data, **kwargs):
        operation = req.params.get('operation', None)
        if not operation:
            raise exceptions.ValidationError(message=_('missing query: operation, eg. ?operation=confirm/discard'))
        return self.make_resource(req).update_state(data, operation)


class CiDelete(Item):
    allow_methods = ('POST', )
    name = 'artifacts.cidelete'
    resource = package_api.CiTypes

    def update(self, req, data, **kwargs):
        return self.make_resource(req).batch_delete(data, **kwargs)


class CollectionDiffConfigs(Collection):
    allow_methods = ('GET', )
    name = 'artifacts.diffconfigs'
    resource = package_api.DiffConfig


class CollectionOnlyInRemoteNexusPackages(POSTCollection):
    allow_methods = ('POST', )
    name = 'artifacts.only-in-remote-nexus.packages'
    resource = package_api.OnlyInRemoteNexusPackages


class PackageFromRemote(base_controller.Controller):
    allow_methods = ('POST',)
    name = 'artifacts.fromremote'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        resp.json = self.resource().upload_and_create2(req.json, **kwargs)
        resp.status = falcon.HTTP_200
        
class DownloadComposePackage(base_controller.Controller):
    allow_methods = ('GET',)
    name = 'artifacts.downloadcomposepackage'
    resource = package_api.UnitDesignPackages

    def on_get(self, req, resp, **kwargs):
        filename,fileobj,filesize = self.resource().download_compose_package(**kwargs)
        resp.set_stream(fileobj, filesize)
        resp.set_header('Content-Disposition', 'attachment;filename="%s"' % urllib.parse.quote(os.path.basename(filename)))
        resp.set_header('Content-Type', 'application/octet-stream')
        resp.status = falcon.HTTP_200
        
class PushComposePackage(base_controller.Controller):
    allow_methods = ('POST',)
    name = 'artifacts.pushcomposepackage'
    resource = package_api.UnitDesignPackages

    def on_post(self, req, resp, **kwargs):
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': self.resource().push_compose_package(**kwargs),
            'message': 'success'
        }
        resp.status = falcon.HTTP_200
        
class SystemConfig(base_controller.Controller):
    allow_methods = ('GET',)
    name = 'artifacts.systemconfig'
    resource = package_api.UnitDesignPackages

    def on_get(self, req, resp, **kwargs):
        local_nexus_server = CONF.nexus.server
        remote_nexus_server = CONF.wecube.nexus.server
        push_nexus_server = CONF.pushnexus.server
        local_nexus_server = local_nexus_server.strip()
        remote_nexus_server = local_nexus_server.strip()
        push_nexus_server = local_nexus_server.strip()
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            local_nexus_server = remote_nexus_server
        resp.json = {
            'code': 200,
            'status': 'OK',
            'data': {
                'upload_enabled': utils.bool_from_string(CONF.wecube.upload_enabled) and local_nexus_server,
                'upload_from_nexus_enabled': utils.bool_from_string(CONF.wecube.upload_nexus_enabled) and remote_nexus_server,
                'push_to_nexus_enabled': True if push_nexus_server else False,
            },
            'message': 'success'
        }
        resp.status = falcon.HTTP_200