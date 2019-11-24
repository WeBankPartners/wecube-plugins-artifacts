from platten/alpine-oracle-jre8-docker
LABEL maintainer = "Webank CTB Team"
ADD target/artifacts-core-0.0.1-SNAPSHOT.jar /application/wecube-plugins-artifacts.jar
ADD build/start.sh /scripts/start.sh
RUN chmod +x /scripts/start.sh
CMD ["/bin/sh","-c","/scripts/start.sh $WECMDB_SERVER_URL $SALTSTACK_SERVER_URL"]
