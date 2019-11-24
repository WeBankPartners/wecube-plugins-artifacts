#!/bin/sh
mkdir -p /log
java -jar /application/wecube-plugins-artifact.jar  \
--server.address=0.0.0.0 \
--server.port=8081 \
--plugins.wecmdb-server-url=$1 \
--plugins.saltstack-server-url >>/log/wecube-plugins-artifacts.log 
