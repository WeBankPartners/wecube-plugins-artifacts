#!/bin/sh
/bin/sh /scripts/tomcat_exporter/start.sh
mkdir -p /log
java -Duser.timezone=Asia/Shanghai \
-Dcom.sun.management.jmxremote \
-Dcom.sun.management.jmxremote.port=18082 \
-Dcom.sun.management.jmxremote.rmi.port=18082 \
-Dcom.sun.management.jmxremote.authenticate=false \
-Dcom.sun.management.jmxremote.ssl=false \
-jar /application/wecube-plugins-artifacts.jar  \
--server.address=0.0.0.0 \
--server.port=8081 \
--plugins.wecube-gateway-server-url=$1 \
--plugins.artifacts-s3-server-url=$2 \
--plugins.artifacts-s3-access-key=$3 \
--plugins.artifacts-s3-secret-key=$4 \
--plugins.artifacts-nexus-server-url=$5 \
--plugins.artifacts-nexus-username=$6 \
--plugins.artifacts-nexus-password=$7 \
--plugins.artifacts_nexus_repository=$8 \
--plugins.cmdb_artifact_path=$9 \
--plugins.jwt-signing-key=${10} >>/log/wecube-plugins-artifacts.log
