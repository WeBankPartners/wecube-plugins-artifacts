#!/bin/sh
mkdir -p /log
java -jar /application/wecube-plugins-artifacts.jar  \
--server.address=0.0.0.0 \
--server.port=8081 \
--plugins.wecmdb-server-url=$1 \
--plugins.saltstack-server-url=$2 \
--plugins.artifacts-s3-server-url=$3 \
--plugins.artifacts-s3-access-key=$4 \
--plugins.artifacts-s3-secret-key=$5 >>/log/wecube-plugins-artifacts.log 
