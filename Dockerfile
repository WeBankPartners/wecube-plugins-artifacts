from platten/alpine-oracle-jre8-docker
LABEL maintainer = "Webank CTB Team"
ADD artifacts-core/target/artifacts-core-0.0.1-SNAPSHOT.jar /application/wecube-plugins-artifacts.jar
ADD build/start.sh /scripts/start.sh
RUN chmod +x /scripts/start.sh
CMD ["/bin/sh","-c","/scripts/start.sh $WECUBE_GATEWAY_SERVER_URL $ARTIFACTS_S3_SERVER_URL $ARTIFACTS_S3_ACCESS_KEY $ARTIFACTS_S3_SECRET_KEY"]
