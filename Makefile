current_dir=$(shell pwd)
version=$(shell bash ./build/version.sh)
date=$(shell date +%Y%m%d%H%M%S)
project_name=$(shell basename "${current_dir}")
remote_docker_image_registry=ccr.ccs.tencentyun.com/webankpartners/wecube-plugins-artifacts
arch ?= amd64          # 默认amd64，可选 ARCH=amd64/arm64
with_nexus ?= true     # 默认true，可选 WITH_NEXUS=true/false
dockerfile := $(if $(with_nexus),Dockerfile,Dockerfile_nonexus)


clean:
	rm -rf $(current_dir)/artifacts-corepy/dist/

build: clean
	pip3 install wheel
	cd artifacts-corepy && python3 setup.py bdist_wheel
	cd artifacts-ui &&  npm install --force && NODE_OPTIONS="--openssl-legacy-provider" npm run plugin

image: build
	ifeq ($(with_nexus),true)
		wget -O nexus-data.tar.gz https://wecube-1259801214.cos.ap-guangzhou.myqcloud.com/nexus-data/nexus-data.tar.gz
	endif
	ifeq ($(arch),arm64)
		docker buildx create --use || true
		docker buildx inspect --bootstrap
		docker buildx build --platform linux/arm64 -t $(project_name):$(version) -f $(dockerfile) .
	else
		docker build -t $(project_name):$(version) -f $(dockerfile) .
	endif

package: image
	rm -rf package
	mkdir -p package
	cd package && docker save $(project_name):$(version) -o image.tar
	cd package && cp ../register.xml .
	cd package && cp ../init.sql ./init.sql
	cd package && sed -i "s~{{REPOSITORY}}~$(project_name)~g" register.xml
	cd package && sed -i "s~{{VERSION}}~$(version)~g" register.xml
	cd artifacts-ui/dist && zip -r ui.zip .
	cd package && cp ../artifacts-ui/dist/ui.zip .
	cd package && zip -r $(project_name)-$(version)-$(arch).zip .
	docker rmi $(project_name):$(version)

upload: package
	$(eval container_id:=$(shell docker run -v $(current_dir)/package:/package -itd --entrypoint=/bin/sh minio/mc))
	docker exec $(container_id) mc config host add wecubeS3 $(s3_server_url) $(s3_access_key) $(s3_secret_key) wecubeS3
	docker exec $(container_id) mc cp /package/$(project_name)-$(version)-$(arch).zip wecubeS3/wecube-plugin-package-bucket
	docker stop $(container_id)
	docker rm -f $(container_id)
	rm -rf $(project_name)-$(version)-$(arch).zip