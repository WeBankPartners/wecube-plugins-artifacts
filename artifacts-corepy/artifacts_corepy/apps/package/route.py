# coding=utf-8

from __future__ import absolute_import

from talos.core import config
from talos.core import utils
from artifacts_corepy.apps.package import controller
from artifacts_corepy.common import nexus

CONF = config.CONF


class SinkAdapter(object):
    def __call__(self, req, resp, repository):
        if utils.bool_from_string(CONF.use_remote_nexus_only):
            client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username, CONF.wecube.nexus.password)
        else:
            client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
        with client.download_stream(client.server + '/repository/' + repository) as stream:
            print(stream.headers)
            resp.set_stream(stream.raw, int(stream.headers.get('Content-Length', 0)))
            resp.set_header('Content-Disposition', stream.headers.get('Content-Disposition'))
            resp.set_header('Content-Type', stream.headers.get('Content-Type'))


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
    api.add_sink(SinkAdapter(), r'/artifacts/repository/(?P<repository>.*)')
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
    api.add_route('/artifacts/platform/v1/packages/wecmdb/entities/diff_configuration/update',
                  controller.ItemDiffConfigUpdate())
    api.add_route('/packages/auto-create-deploy-package', controller.ItemUploadAndCreatePackage())
