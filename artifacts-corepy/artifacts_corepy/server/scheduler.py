# coding=utf-8
"""
artifacts_corepy.server.scheduler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供定时清理能力

"""

from __future__ import absolute_import

import os
import shutil
import time
import datetime
import logging
from pytz import timezone
from talos.core import config

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from artifacts_corepy.server.wsgi_server import application
from artifacts_corepy.common import nexus
from artifacts_corepy.common import wecmdbv2 as wecmdb
from artifacts_corepy.common import wecube

CONF = config.CONF
LOG = logging.getLogger(__name__)

jobstores = {'default': MemoryJobStore()}
executors = {'default': ThreadPoolExecutor(5)}
job_defaults = {'coalesce': False, 'max_instances': 1}


def cleanup_cached_dir():
    try:
        max_delta = 24 * 60 * 60
        base_dir = CONF.pakcage_cache_dir
        for name in list(os.listdir(base_dir)):
            fullpath = os.path.join(base_dir, name)
            if os.path.isdir(fullpath):
                path_stat = os.stat(fullpath)
                if time.time() - path_stat.st_atime > max_delta:
                    LOG.info('remove dir: %s, last access: %s', fullpath, path_stat.st_atime)
                    shutil.rmtree(fullpath, ignore_errors=True)
    except Exception as e:
        LOG.exception(e)


def rotate_log():
    try:
        logs = [CONF.log.gunicorn_access, CONF.log.gunicorn_error, CONF.log.path]
        extend_logs = getattr(CONF.log, 'loggers', [])
        for l in extend_logs:
            if l.get('path'):
                logs.append(l['path'])
        max_file_keep = 30
        for log_file in logs:
            results = []
            base_dir = os.path.dirname(log_file)
            if os.path.exists(base_dir):
                for name in list(os.listdir(base_dir)):
                    fullpath = os.path.join(base_dir, name)
                    if os.path.isfile(fullpath):
                        if fullpath.startswith(log_file + '.'):
                            timestamp = 0
                            try:
                                timestamp = int(fullpath.rsplit('.', 1)[1])
                                # ignore which not endswith datetime
                                results.append((timestamp, fullpath))
                            except Exception as e:
                                pass

            results.sort(key=lambda item: item[0])
            while len(results) >= max_file_keep:
                timestamp, fullpath = results.pop(0)
                try:
                    LOG.info('remove file: %s', fullpath)
                    os.remove(fullpath)
                except Exception as e:
                    LOG.info('remove file: %s error: %s', fullpath, str(e))
        for log_file in logs:
            new_log_file = log_file + '.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            if os.path.exists(log_file):
                try:
                    LOG.info('rename file: %s to %s', log_file, new_log_file)
                    os.rename(log_file, new_log_file)
                except Exception as e:
                    LOG.info('rename file: %s to %s error: %s', log_file, new_log_file, str(e))
    except Exception as e:
        LOG.exception(e)


def cleanup_deploy_package():
    try:
        wecube_client = wecube.WeCubeClient(CONF.wecube.server, "")
        wecube_client.login_subsystem()
        cmdb_client = wecmdb.WeCMDBClient(CONF.wecube.server, wecube_client.token)
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [],
            "paging": False,
            "sorting": {
                "asc": False,
                "field": "update_time"
            }
        }
        resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            return
        unit_design_list = resp_json['data']['contents']

        nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)
        artifact_repository = CONF.nexus.repository

        for unit_design in unit_design_list:
            query = {
                "dialect": {
                    "queryMode": "new"
                },
                "filters": [{
                    "name": "unit_design",
                    "operator": "eq",
                    "value": unit_design["guid"]
                }],
                "paging": False,
                "sorting": {
                    "asc": False,
                    "field": "update_time"
                }
            }
            resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
            if not resp_json.get('data', {}).get('contents', []):
                continue

            keep_topn = unit_design.get(CONF.cleanup.keep_unit_field, CONF.cleanup.keep_topn)
            keep_topn = int(keep_topn)
            deploy_package_list = resp_json['data']['contents']
            cnt = 1
            for deploy_package in deploy_package_list:
                if deploy_package['state'] == 'deleted_0':
                    continue
                if cnt > keep_topn:
                    try:
                        data = [{'guid': deploy_package["guid"]}]
                        resp_json = cmdb_client.delete(CONF.wecube.wecmdb.citypes.deploy_package, data)
                        if resp_json.get('statusCode', 'OK') == 'OK' and resp_json['data'][0].get('state',
                                                                                                '') == 'deleted_0':
                            LOG.info('delete package[%s] from ci data', deploy_package["guid"])
                            cmdb_client.confirm(CONF.wecube.wecmdb.citypes.deploy_package, data)
                        if resp_json.get('statusCode', 'OK') == 'OK':
                            deploy_package_url = deploy_package.get("deploy_package_url", "")
                            if deploy_package_url.startswith(CONF.wecube.server):
                                # delete nexus package
                                prefix = CONF.wecube.server.rstrip('/') + '/artifacts/repository/' + artifact_repository
                                suffix = deploy_package_url[len(prefix):]
                                suffix_list = suffix.split("/")
                                if len(suffix_list) >= 2:
                                    filename = suffix_list[len(suffix_list) - 1]
                                    component_name = filename
                                    component_group = "/"
                                    if len(suffix_list) > 2:
                                        component_group = suffix[:len(suffix) - len("/" + filename)]
                                        component_name = suffix[1:]
                                    asset_info = nexus_client.get_asset(artifact_repository, component_group,
                                                                        component_name)
                                    if asset_info:
                                        asset_id = asset_info["id"]
                                        nexus_client.delete_assets(artifact_repository,
                                                                '/service/rest/v1/assets/' + asset_id)
                                        LOG.info('delete package[%s] from local nexus: %s', deploy_package["guid"], suffix)
                                    else:
                                        LOG.error('delete package[%s] from local nexus: %s failed, asset not found',
                                                deploy_package["guid"], suffix)
                    except Exception as e:
                        LOG.exception(e)
                cnt += 1
        return
    except Exception as e:
        LOG.exception(e)


def main():
    tz_info = timezone(CONF.timezone)
    try:
        if CONF.platform_timezone:
            tz_info = timezone(CONF.platform_timezone)
    except Exception as e:
        LOG.exception(e)
    scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=tz_info)
    scheduler.add_job(cleanup_cached_dir, 'cron', hour='*')
    scheduler.add_job(rotate_log, 'cron', hour=3, minute=5)

    cron_values = CONF.cleanup.cron.split()
    scheduler.add_job(cleanup_deploy_package,
                      'cron',
                      minute=cron_values[0],
                      hour=cron_values[1],
                      day=cron_values[2],
                      month=cron_values[3],
                      day_of_week=cron_values[4])
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()