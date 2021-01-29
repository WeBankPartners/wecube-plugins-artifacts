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
from talos.core import logging as mylogger

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

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


def main():
    config.setup(os.environ.get('ARTIFACTS_COREPY_CONF', '/etc/artifacts_corepy/artifacts_corepy.conf'),
                 dir_path=os.environ.get('ARTIFACTS_COREPY_CONF_DIR', '/etc/artifacts_corepy/artifacts_corepy.conf.d'))
    mylogger.setup()
    tz_info = timezone(CONF.timezone)
    try:
        if CONF.platform_timezone:
            prefix = 'ENV@'
            value = CONF.platform_timezone
            if value.startswith(prefix):
                env_name = value[len(prefix):]
                value = os.getenv(env_name, default='')
            tz_info = timezone(value)
    except Exception as e:
        LOG.exception(e)
    scheduler = BlockingScheduler(jobstores=jobstores,
                                  executors=executors,
                                  job_defaults=job_defaults,
                                  timezone=tz_info)
    scheduler.add_job(cleanup_cached_dir, 'cron', hour='*')
    scheduler.add_job(rotate_log, 'cron', hour=3, minute=5)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()