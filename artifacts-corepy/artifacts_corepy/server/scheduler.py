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
from talos.core import utils

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
        interval_min = 10
        try:
            interval_min = int(CONF.pakcage_cache_cleanup_interval_min)
        except Exception as e:
            LOG.error("Invalid package_cache_cleanup_interval_min: %s",
                      CONF.pakcage_cache_cleanup_interval_min)
        max_delta = interval_min * 60
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


def download_url_parse(url):
    ret = {}
    results = url.split('/repository/', 1)
    ret['server'] = results[0]
    ret['fullpath'] = '/repository/' + results[1]
    results = results[1].split('/', 1)
    ret['repository'] = results[0]
    ret['filename'] = results[1].split('/')[-1]
    if results[1].count('/') >= 1:
        ret['group'] = '/' + results[1].rsplit('/', 1)[0]
    else:
        ret['group'] = '/'
    return ret

def delete_nexus_package(nexus_client, deploy_package_url):
    if deploy_package_url.startswith(CONF.wecube.server):
        # delete nexus package
        parsed_result = download_url_parse(deploy_package_url)
        # delete nexus package
        component_group = parsed_result['group']
        component_name = parsed_result['group'].rstrip('/') + '/' + parsed_result['filename'].lstrip('/')
        asset_info = nexus_client.get_asset(parsed_result['repository'], component_group,
                                                component_name)
        if asset_info:
            asset_id = asset_info["id"]
            nexus_client.delete_assets(parsed_result['repository'],
                                    '/service/rest/v1/assets/' + asset_id)
            LOG.info('delete package[%s-%s] from local nexus: %s', asset_info["id"], parsed_result['filename'], deploy_package_url)
        else:
            LOG.warn('delete package from local nexus: %s failed, asset not found', deploy_package_url)
        return True
    return False

def get_deploy_package_by_id(cmdb_client, deploy_package_id):
    query = {
        "dialect": {
            "queryMode": "new"
        },
        "filters": [{
            "name": "guid",
            "operator": "eq",
            "value": deploy_package_id
        }],
        "paging": False
    }
    resp_json = cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
    if not resp_json.get('data', {}).get('contents', []):
        return None
    return resp_json['data']['contents'][0]

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

        if utils.bool_from_string(CONF.use_remote_nexus_only):
            nexus_client = nexus.NeuxsClient(CONF.wecube.nexus.server, CONF.wecube.nexus.username,
                                                CONF.wecube.nexus.password)
        else:
            nexus_client = nexus.NeuxsClient(CONF.nexus.server, CONF.nexus.username, CONF.nexus.password)

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
                if cnt > keep_topn:
                    try:
                        data = [{'guid': deploy_package["guid"]}]
                        deploy_package_url = deploy_package.get("deploy_package_url", "")
                        if deploy_package['state'] == 'deleted_0':
                            delete_nexus_package(nexus_client, deploy_package_url)
                            # do confirm
                            cmdb_client.confirm(CONF.wecube.wecmdb.citypes.deploy_package, data)
                        else:
                            resp_json = cmdb_client.delete(CONF.wecube.wecmdb.citypes.deploy_package, data)
                            if resp_json.get('statusCode', 'OK') == 'OK':
                                LOG.info('delete package[%s] from ci data', deploy_package["guid"])
                                delete_nexus_package(nexus_client, deploy_package_url)
                                requery_deploy_package = get_deploy_package_by_id(cmdb_client, deploy_package["guid"])
                                # do confirm if needed 
                                if requery_deploy_package is not None and requery_deploy_package.get('state','') == 'deleted_0':
                                    cmdb_client.confirm(CONF.wecube.wecmdb.citypes.deploy_package, data)
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
    scheduler.add_job(cleanup_cached_dir, 'cron', minute="*/5")
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