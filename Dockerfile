from sonatype/nexus3:3.27.0
LABEL maintainer = "Webank CTB Team"
USER root
ADD build/Centos-8.repo /etc/yum.repos.d/
ADD artifacts-corepy/requirements.txt /tmp/requirements.txt
ADD artifacts-corepy/dist/* /tmp/
RUN mkdir -p /etc/artifacts_corepy/
RUN mkdir -p /var/log/artifacts_corepy/
ADD artifacts-corepy/etc/* /etc/artifacts_corepy/
ADD nexus-data.tar.gz /nexus-data-init
# Install && Clean up
RUN yum clean all && yum makecache && yum install -y python3 python3-devel gcc libev-devel make  && \
    pip3 install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r /tmp/requirements.txt && \
    pip3 install /tmp/*.whl
ADD build/start_all.sh /scripts/start_all.sh
RUN chmod +x /scripts/start_all.sh
CMD ["/bin/sh","-c","/scripts/start_all.sh"]