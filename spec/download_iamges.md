# 物料包列表支持镜像导出功能

## 需求背景
用户需要在物料包列表实现镜像导出功能，单独提供一个镜像导出按钮，点击按钮，可以导出物料包关联的镜像，导出的镜像为tar文件类型

## 功能描述
**步骤如下**
1. 物料包列表页面操作栏提供镜像下载按钮
2. 用户点击镜像下载按钮，调用镜像下载接口download-image
3. 下载镜像时，需要找出物料包关联的镜像名称image_name，然后找出当前源镜像仓库配置CONF.image，包括仓库server_url、username、password
4. 使用skopeo将镜像仓库对应的image_name下载到物料包部署机器临时空间，该下载过程为流式传输，同时浏览器调用镜像下载接口时，再从部署机器临时空间将镜像下载到用户浏览器，下载的镜像格式为tar文件类型，该下载过程也是流式传输
5. 下载接口执行成功或失败，需要自动回收清理拉取的镜像文件

## 涉及配置
| 配置项 | 描述 |
|-------|------|
| CONF.image.server_url | 源镜像仓库地址 |
| CONF.image.username | 源镜像仓库用户名 |
| CONF.image.password | 源镜像仓库密码 |


## 注意事项
- 镜像保存使用 `skopeo copy docker://... docker-archive:image_xxx.tar` 命令。

## 代码文件
对应的代码文件在 `/artifacts_corepy/apps/package/apiv2.py`
