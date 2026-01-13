### 镜像推送功能

#### 功能概述
在物料包推送过程中，自动检查并推送关联的Docker镜像。

#### 配置参数
- **源仓库**: 固定为 `172.21.10.202:8083`，用户名 `admin`，密码 `artifacts`
- **目标仓库**: 从系统参数 `PUSH_IMAGE_SERVER_URL`、`PUSH_IMAGE_USERNAME`、`PUSH_IMAGE_PASSWORD` 读取

#### 实现逻辑
1. 在一键推包功能中，检查物料包的 `image_name` 字段是否有值
2. 如果 `image_name` 字段不为空，说明存在关联镜像
3. 如果镜像名称不包含版本号，自动添加 `:latest` 标签
4. 使用 `skopeo copy` 命令将镜像从源仓库推送到目标仓库

#### 推送命令示例
```bash
skopeo copy \
  --all \
  --src-creds admin:artifacts \
  --dest-creds ${PUSH_IMAGE_USERNAME}:${PUSH_IMAGE_PASSWORD} \
  --src-tls-verify=false \
  --dest-tls-verify=false \
  docker://172.21.10.202:8083/nginx:latest \
  docker://${PUSH_IMAGE_SERVER_URL}/nginx:latest
```

#### 错误处理
- 镜像推送失败不会影响物料包推送的成功
- 详细记录推送日志，便于问题排查
- 支持超时控制（默认10分钟）

#### 代码实现状态
- ✅ 已添加 `image_name` 字段到物料包数据结构
- ✅ 已添加镜像推送配置参数到配置文件
- ✅ 已实现镜像推送逻辑 (`_push_docker_image` 方法)
- ✅ 已集成到 `push_compose_package` 方法中
- ✅ 已确保Docker镜像包含skopeo工具
- ✅ 已修复方法定义位置问题（移至正确的类中）
