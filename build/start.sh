#!/bin/sh
mkdir -p /log
java -jar /application/wecube-plugins-artifacts.jar  \
--server.address=0.0.0.0 \
--server.port=8081 \
--plugins.wecube-platform-server-url=$1 \
--plugins.wecmdb-server-url=$2 \
--plugins.saltstack-server-url=$3 \
--plugins.artifacts-s3-server-url=$4 \
--plugins.artifacts-s3-access-key=$5 \
--plugins.artifacts-s3-secret-key=$6 >>/log/wecube-plugins-artifacts.log 
