# coding=utf-8

from __future__ import absolute_import

from talos.core import config
from talos.core import utils
from talos.core.i18n import _
from artifacts_corepy.apps.package import controller
from artifacts_corepy.common import nexus
from artifacts_corepy.common import wecube
from artifacts_corepy.common import exceptions

CONF = config.CONF


class DownloadAdapter(object):
    def __call__(self, req, resp, repository):
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username, CONF.wecube.nexus.password)
        else:
            client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
        with client.download_stream(client.server + '/repository/' + repository) as stream:
            resp.set_stream(stream.raw, int(stream.headers.get('Content-Length', 0)))
            resp.set_header('Content-Disposition', stream.headers.get('Content-Disposition'))
            resp.set_header('Content-Type', stream.headers.get('Content-Type'))


class EntityAdapter(object):
    def __call__(self, req, resp, package_name, entity_name, action_name):
        server = CONF.wecube.server
        token = req.auth_token
        client = wecube.WeCubeClient(server, token)
        url = '/platform/v1/packages/%(package_name)s/entities/%(entity_name)s/%(action_name)s' % {
            'package_name': package_name,
            'entity_name': entity_name,
            'action_name': action_name,
        }
        if action_name == 'retrieve':
            data = client.retrieve(url)
            resp.json = {'code': 200, 'status': 'OK', 'data': data['data'], 'message': 'success'}
        elif action_name == 'update':
            data = client.update(url, req.json)
            resp.json = {'code': 200, 'status': 'OK', 'data': data['data'], 'message': 'success'}
        else:
            raise exceptions.NotFoundError(
                _('%(action_name)s for %(package_name)s:%(entity_name)s not supported') % {
                    'package_name': package_name,
                    'entity_name': entity_name,
                    'action_name': action_name,
                })


def add_routes(api):
    api.add_route('/artifacts/system-design-versions', controller.CollectionSystemDesign())
    api.add_route('/artifacts/system-design-versions/{rid}', controller.ItemSystemDesign())
    api.add_route('/artifacts/getPackageCiTypeId', controller.ControllerDeployPackageCiTypeId())
    api.add_route('/artifacts/static-data/special-connector', controller.CollectionSpecialConnector())
    api.add_route('/artifacts/ci-types', controller.CollectionCiTypes())
    api.add_route('/artifacts/enum/system/codes', controller.CollectionEnumCodes())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/query', controller.CollectionUnitDesignPackages())
    # Nexus
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/queryNexusDirectiry',
                  controller.CollectionUnitDesignNexusPackages())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/uploadNexusPackage',
                  controller.CollectionUnitDesignNexusPackageUpload())
    # local upload
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/upload',
                  controller.CollectionUnitDesignPackageUpload())
    # artifact download
    api.add_sink(DownloadAdapter(), r'/artifacts/repository/(?P<repository>.*)')
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/query',
                  controller.ItemPackage())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/comparison',
                  controller.UnitDesignPackageBaselineCompare())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/files/comparison',
                  controller.UnitDesignPackageBaselineFilesCompare())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/files/query',
                  controller.UnitDesignPackageFileTree())
    api.add_route('/artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/update',
                  controller.ItemPackageUpdate())
    api.add_route('/artifacts/packages/auto-create-deploy-package', controller.ItemUploadAndCreatePackage())
    api.add_route('/artifacts/ci-types/{ci_type_id}/references/by', controller.ItemCiReferences())
    api.add_route('/artifacts/ci-types/{ci_type_id}/attributes', controller.ItemCiAttributes())

    api.add_route('/artifacts/ci/state/operate', controller.CiStateAction())
    api.add_route('/artifacts/ci-types/{ci_type_id}/ci-data/batch-delete', controller.CiDelete())
    # api.add_route('/artifacts/platform/v1/packages/wecmdb/entities/diff_configuration/retrieve',
    #               controller.CollectionDiffConfigs())
    # api.add_route('/artifacts/platform/v1/packages/wecmdb/entities/diff_configuration/update',
    #               controller.ItemDiffConfigUpdate())
    api.add_sink(
        EntityAdapter(),
        r'/artifacts/platform/v1/packages/(?P<package_name>[-_A-Za-z0-9]+)/entities/(?P<entity_name>[-_A-Za-z0-9]+)/(?P<action_name>[-_A-Za-z0-9]+)'
    )