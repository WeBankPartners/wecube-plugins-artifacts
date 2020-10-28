# from platten/alpine-oracle-jre8-docker
# LABEL maintainer = "Webank CTB Team"
# ADD artifacts-core/target/artifacts-core-0.0.1-SNAPSHOT.jar /application/wecube-plugins-artifacts.jar
# ADD build/start.sh /scripts/start.sh
# RUN chmod +x /scripts/start.sh
# ADD build/tomcat_exporter.tar /scripts/
# CMD ["/bin/sh","-c","/scripts/start.sh $WECUBE_GATEWAY_SERVER_URL $ARTIFACTS_S3_SERVER_URL $ARTIFACTS_S3_ACCESS_KEY $ARTIFACTS_S3_SECRET_KEY $ARTIFACTS_NEXUS_SERVER_URL $ARTIFACTS_NEXUS_USERNAME $ARTIFACTS_NEXUS_PASSWORD $ARTIFACTS_NEXUS_REPOSITORY $CMDB_ARTIFACT_PATH $JWT_SIGNING_KEY"]

from sonatype/nexus3:3.27.0
LABEL maintainer = "Webank CTB Team"
USER root
ADD build/Centos-8.repo /etc/yum.repos.d/
ADD artifacts-corepy/requirements.txt /tmp/requirements.txt
ADD artifacts-corepy/dist/* /tmp/
RUN mkdir -p /etc/artifacts-corepy/
RUN mkdir -p /var/log/artifacts-corepy/
ADD artifacts-corepy/etc/* /etc/artifacts-corepy/
ADD nexus-data.tar.gz /nexus-data
# Install && Clean up
RUN yum clean all && yum makecache && yum install -y python3 python3-devel gcc libev-devel make  && \
RUN pip3 install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r /tmp/requirements.txt && \
    pip3 install /tmp/*.whl && 
USER nexus
CMD ["nohup", "sh" "-c" "${SONATYPE_DIR}/start-nexus-repository-manager.sh", "&"]
USER root
CMD ["/usr/local/bin/gunicorn", "--config", "/etc/artifacts-corepy/gunicorn.py", "artifacts_corepy.server.wsgi_server:application"]