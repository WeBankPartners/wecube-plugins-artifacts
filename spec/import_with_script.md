# 物料包导入时支持写入image_deploy_script的值

## 需求背景
用户需要在导入物料包的时候，如果物料包相关属性image_deploy_script有值，需要将该值一起导入到对应的单元下。

## 功能描述
**步骤如下**
1. 用户选择本地上传物料包时，需要将物料包对应image_deploy_script的值也导入进来。
2. 用户选择在线上传物料包时，需要将物料包对应image_deploy_script的值也导入进来。
3. 组合包和应用包都需要实现上述逻辑。

## 代码文件
对应的代码文件在/artifacts_corepy/apps/package/apiv2.py