#!/bin/sh
if [ ${ARTIFACTS_USE_REMOTE_NEXUS_ONLY} == 'true' ]; then
    echo "use remote nexus only, skip local nexus"
else
    echo "use local nexus, starting local nexus"
    if [ -d '/nexus-data/db' ] && [ `ls /nexus-data/db|wc -l` -gt 0 ];then
        echo 'nexus data already inited...'
    else
        echo 'nexus data is not ready, copy init data...'
        cp -rf /nexus-data-init/ /nexus-data/
    fi
    nohup ${SONATYPE_DIR}/start-nexus-repository-manager.sh > /dev/null 2>&1 &
fi
nohup artifacts_corepy_scheduler > /dev/null 2>&1 &
/usr/local/bin/gunicorn --config /etc/artifacts_corepy/gunicorn.py artifacts_corepy.server.wsgi_server:application
