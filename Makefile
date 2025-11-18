current_dir=$(shell pwd)
version=$(shell bash ./build/version.sh)
date=$(shell date +%Y%m%d%H%M%S)
project_name=$(shell basename "${current_dir}")
remote_docker_image_registry=ccr.ccs.tencentyun.com/webankpartners/wecube-plugins-artifacts
with_nexus='true'

clean_py:
	rm -rf $(current_dir)/artifacts-corepy/dist/

build_py: clean_py
	pip3 install wheel
	cd artifacts-corepy && python3 setup.py bdist_wheel
	cd artifacts-ui &&  npm install --force && npm run plugin

image_py: build_py
	wget -O nexus-data.tar.gz https://wecube-1259801214.cos.ap-guangzhou.myqcloud.com/nexus-data/nexus-data.tar.gz
	@if [ $(with_nexus) == 'true' ]; \
	then \
		docker build -t $(project_name):$(version) .; \
	else \
		docker build -t $(project_name):$(version) -f Dockerfile_nonexus .; \
	fi

package_py: image_py
	rm -rf package
	mkdir -p package
	cd package && docker save $(project_name):$(version) -o image.tar
	cd package && cp ../register.xml .
	cd package && cp ../init.sql ./init.sql
	cd package && sed -i "s~{{REPOSITORY}}~$(project_name)~g" register.xml
	cd package && sed -i "s~{{VERSION}}~$(version)~g" register.xml
	cd artifacts-ui/dist && zip -r ui.zip .
	cd package && cp ../artifacts-ui/dist/ui.zip .
	cd package && zip -r $(project_name)-$(version).zip .
	docker rmi $(project_name):$(version)

upload_py: package_py
	$(eval container_id:=$(shell docker run -v $(current_dir)/package:/package -itd --entrypoint=/bin/sh minio/mc))
	docker exec $(container_id) mc config host add wecubeS3 $(s3_server_url) $(s3_access_key) $(s3_secret_key) wecubeS3
	docker exec $(container_id) mc cp /package/$(project_name)-$(version).zip wecubeS3/wecube-plugin-package-bucket
	docker stop $(container_id)
	docker rm -f $(container_id)
	rm -rf $(project_name)-$(version).zip


image_py_arm64: build_py_arm64
	
	@if [ $(with_nexus) == 'true' ]; \
	then \
	    wget -O nexus-data.tar.gz https://wecube-1259801214.cos.ap-guangzhou.myqcloud.com/nexus-data/nexus-data.tar.gz; \
		docker build -t $(project_name):$(version) .; \
	else \
	    docker buildx create --use; \
		docker buildx inspect --bootstrap; \
		docker buildx build --build-arg TARGETARCH=arm64 --platform linux/arm64 -t $(project_name):$(version) -f Dockerfile_nonexus .; \
	fi

package_py_arm64: image_py_arm64
	rm -rf package
	mkdir -p package
	cd package && docker save $(project_name):$(version) -o image.tar
	cd package && cp ../register.xml .
	cd package && cp ../init.sql ./init.sql
	cd package && sed -i "s~{{REPOSITORY}}~$(project_name)~g" register.xml
	cd package && sed -i "s~{{VERSION}}~$(version)~g" register.xml
	cd artifacts-ui/dist && zip -r ui.zip .
	cd package && cp ../artifacts-ui/dist/ui.zip .
	cd package && zip -r $(project_name)-$(version).zip .
	docker rmi $(project_name):$(version)

upload_py_arm64: package_py_arm64
	$(eval container_id:=$(shell docker run -v $(current_dir)/package:/package -itd --entrypoint=/bin/sh minio/mc))
	docker exec $(container_id) mc config host add wecubeS3 $(s3_server_url) $(s3_access_key) $(s3_secret_key) wecubeS3
	docker exec $(container_id) mc cp /package/$(project_name)-$(version).zip wecubeS3/wecube-plugin-package-bucket
	docker stop $(container_id)
	docker rm -f $(container_id)
	rm -rf $(project_name)-$(version).zip