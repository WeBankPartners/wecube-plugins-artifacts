
接口说明：
组合物料包：包含原始物料包，包的配置，差异化变量配置信息，便于跨环境的物料使用

1. 导出组合物料包：
   即下载组合物料包到本地文件系统
   GET /artifacts/packages/{deploy_package_id}/download
   响应：文件流下载
2. 推送组合物料包：
   推送组合物料包到指定nexus上，nexus通过系统参数PUSH_NEXUS_\*配置
   POST /artifacts/unit-designs/{unit_design_id}/packages/{deploy_package_id}/push
   请求：json {}
   响应：新包配置数据