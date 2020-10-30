#!/bin/sh
if [ ${ARTIFACTS_USE_REMOTE_NEXUS_ONLY} == 'true' ]; then
    echo "use remote nexus only, skip local nexus"
else
    echo "use local nexus, starting local nexus"
    nohup ${SONATYPE_DIR}/start-nexus-repository-manager.sh > /var/log/artifacts_corepy/nexus.log &
fi
/usr/local/bin/gunicorn --config /etc/artifacts_corepy/gunicorn.py artifacts_corepy.server.wsgi_server:application
