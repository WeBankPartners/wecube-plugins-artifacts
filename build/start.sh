#!/bin/sh
mkdir -p /log
java -Duser.timezone=Asia/Shanghai -jar /application/wecube-plugins-artifacts.jar  \
--server.address=0.0.0.0 \
--server.port=8081 \
--plugins.wecube-gateway-server-url=$1 \
--plugins.artifacts-s3-server-url=$2 \
--plugins.artifacts-s3-access-key=$3 \
--plugins.artifacts-s3-secret-key=$4 >>/log/wecube-plugins-artifacts.log 
