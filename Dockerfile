FROM ccr.ccs.tencentyun.com/webankpartners/nexus3:3.86.2
LABEL maintainer = "Webank CTB Team"
USER root
RUN rm -f /etc/yum.repos.d/redhat.repo /etc/yum.repos.d/ubi.repo
ADD build/Centos-9.repo /etc/yum.repos.d/base.repo
ADD artifacts-corepy/requirements.txt /tmp/requirements.txt
ADD artifacts-corepy/dist/* /tmp/
RUN mkdir -p /etc/artifacts_corepy/
RUN mkdir -p /var/log/artifacts_corepy/
RUN mkdir -p /tmp/artifacts/
ADD artifacts-corepy/etc/* /etc/artifacts_corepy/
ADD nexus-data.tar.gz /nexus-data-init

# Install && Clean up
RUN microdnf clean all && microdnf makecache && microdnf -y install expat python3 python3-devel swig openssl-devel gcc libev-devel make  && \
    pip3 install -i http://mirrors.tencentyun.com/pypi/simple/ --trusted-host mirrors.tencentyun.com -r /tmp/requirements.txt && \
    pip3 install /tmp/*.whl && microdnf -y remove python3-devel swig openssl-devel gcc libev-devel make && rm -rf /tmp/* && microdnf clean all
ADD build/start_all.sh /scripts/start_all.sh
RUN chmod +x /scripts/start_all.sh
CMD ["/bin/sh","-c","/scripts/start_all.sh"]
