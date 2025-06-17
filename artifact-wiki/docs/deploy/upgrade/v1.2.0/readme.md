文档内的差异化说明基于v1.2.0 -> v1.1.0版本

## CMDB新增字段

| CI名称 | 字段  | 字段类型 | 字段含义说明 |
| --- | --- | --- | --- |
| deploy_package(部署物料包) | key_service_code | multiObject | 关键服务交易码，用于监控配置 |
| deploy_package(部署物料包) | diff_conf_directory | text 255(长度请按需调整) | APP差异化配置目录，用于差异化文件自动发现 |
| deploy_package(部署物料包) | script_file_directory | text 255(长度请按需调整) | APP脚本目录，用于脚本文件自动发现 |
| deploy_package(部署物料包) | log_file_directory | text 255(长度请按需调整) | APP日志目录，用于监控配置 |
| deploy_package(部署物料包) | log_file_trade | text 1024(长度请按需调整) | APP Trade日志文件，用于监控配置 |
| deploy_package(部署物料包) | log_file_keyword | text 1024(长度请按需调整) | APP Keyword日志文件，用于监控配置 |
| deploy_package(部署物料包) | log_file_metric | text 1024(长度请按需调整) | APP Metric日志文件，用于监控配置 |
| deploy_package(部署物料包) | log_file_trace | text 1024(长度请按需调整) | APP Trace日志文件，用于监控配置 |
| deploy_package(部署物料包) | db_deploy_file_directory | text 255(长度请按需调整) | DB 部署文件目录，用于全量初始化SQL自动发现 |
| deploy_package(部署物料包) | db_diff_conf_directory | text 255(长度请按需调整) | DB 差异化配置目录，用于差异化SQL文件自动发现 |
| diff_variable(差异化配置项) | variable_type | text 64(长度请按需调整) | 差异化变量类：ENCRYPTED/FILE/PRIVATE/GLOBAL |

###

## 新增API

##### 获取单元Nexus路径：

GET /artifacts/unit-designs/{unit_design_id}/packages/queryNexusPath

返回数据：{'artifact_path': '/'}

##### 查询系统配置（决定是否禁用按钮）

GET /artifacts/sysconfig

返回数据：{

    'code': 200,

    'status': 'OK',

    'data': {

        'upload_enabled': true/false,

        'upload_from_nexus_enabled': true/false,

        'push_to_nexus_enabled': true/false

    },

    'message': 'success'

}

##### 查询物料包的可发起编排列表

GET /artifacts/process/definitions

返回数据：原始platform数据

## API更新

##### 查询Nexus文件列表(新增返回创建时间)：

GET /artifacts/unit-designs/{unit_design_id}/packages/queryNexusDirectiry

返回数据：{

    data: [{...以前字段, "lastModified": "2024-08-28T06:19:24Z"}]

}

##### 在线选包（增加baseline_package参数）

POST /artifacts/unit-designs/{unit_design_id}/packages/uploadNexusPackage?downloadUrl=http://xxxxxxxxx&&baseline_package={deploy_package_id}

{}

[changed]相同的单元下相同的包名替换，不同的单元下相同的包名报错

##### 本地上传(新增form key: baseline_package)

POST /artifacts/unit-designs/{unit_design_id}/packages/upload

content-type: multipart/form-data;

form key: file 文件内容

form key: baseline_package 基线包ID

[changed]相同的单元下相同的包名替换，不同的单元下相同的包名报错

从nexus上传，与在线选包相同，纯接口非页面使用（输入输出无变化，仅对比逻辑更新为目录+文件对比）

POST /artifacts/packages/auto-create-deploy-package

{

    "nexusUrl": "/path/filename.tar.gz",

    "baselinePackage": "基线包ID"

}

返回{"guid": "xxxxxxxxx"}

## 新增差异化变量

新增差异化变量时增加类型：ENCRYPTED, FILE, GLOBAL, PRIVATE

ARTIFACTS_DB_SCRIPT_EXTENSION 数据库文件后缀名，默认.sql

PUSH_NEXUS_SERVER_URL 推送组合包的Nexus地址

PUSH_NEXUS_USERNAME 推送组合包的Nexus用户名

PUSH_NEXUS_PASSWORD 推送组合包的Nexus密码

PUSH_NEXUS_REPOSITORY 推送组合包的Nexus 仓库名

ARTIFACTS_DEPLOY_PACKAGE_FIELD_MAP 部署包字段名映射，当CMDB中字段名和默认值不同时使用，格式{"key_service_code": "monitor_service_code"}，则意味着CMDB中字段名为monitor_service_code

ARTIFACTS_DIFF_CONF_TEMPLATE_MAP 差异化变量符号的默认模板映射，如{"@":"表达式"}，当新增此变量时将自动填写默认表达式。

ARTIFACTS_CACHE_CLEANUP_INTERVAL_MIN 本地缓存包的清理间隔，默认10min

ARTIFACTS_COMPOSE_OVERWRITE_GLOBAL 导入组合包时是否覆盖全局变量，默认false，即忽略且不覆盖，true时有权限则覆盖，没权限则弹出报错

## 功能说明：字段自动填充与Baseline包分析逻辑说明

APP:

差异化目录：

    组合包：目录仅继承，文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，差异化文件清单自动分析(扩展名限制)

        有baseline

            填充输入目录值，差异化文件清单继承删除+继承追加(扩展名限制，去重，保持原顺序)

    无输入值：

        无baseline

            填充默认目录值，差异化文件清单自动分析(扩展名限制)

        有baseline

            baseline目录值空：填充默认目录值，差异化文件清单继承删除+继承追加(扩展名限制，去重，保持原顺序)

            baseline目录值非空：继承baseline值，差异化文件清单继承删除+继承追加(扩展名限制，去重，保持原顺序)

脚本目录

    组合包：目录仅继承，文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，脚本文件清单：无输入则填充默认，否则使用输入值

        有baseline

            填充输入目录值，脚本文件清单：无输入则仅继承，否则使用输入值

    无输入值：

        无baseline

            填充默认目录值，脚本文件清单填充默认

        有baseline

            baseline目录值空：目录值仅继承，脚本文件清单仅继承

            baseline目录值非空：目录值仅继承，脚本文件清单仅继承

日志目录

    组合包：目录仅继承，文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，日志文件清单：无输入则填充默认，否则使用输入值

        有baseline

            填充输入目录值，日志文件清单：无输入则仅继承，否则使用输入值

    无输入值：

        无baseline

            填充默认目录值，日志文件清单填充默认

        有baseline

            baseline目录值空：目录值仅继承，日志文件清单仅继承

            baseline目录值非空：目录值仅继承，日志文件清单仅继承

DB:

差异化目录

    组合包：目录仅继承，文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，差异化文件清单：无输入则填充默认(空)，否则使用输入值

        有baseline

            填充输入目录值，差异化文件清单：无输入则填充默认(空)，否则使用输入值  （原：无输入则仅继承）

    无输入值：

        无baseline

            填充默认目录值，差异化文件清单填充默认(空)

        有baseline

            baseline目录值空：目录值仅继承，差异化文件清单填充默认(空) （原：差异化文件清单仅继承）

            baseline目录值非空：目录值仅继承，差异化文件清单填充默认(空) （原：差异化文件清单仅继承）

升级目录

    有输入值：

        无baseline

            填充输入目录值，文件清单自动分析(扩展名限制)

        有baseline

            填充输入目录值，文件清单仅追加

    无输入值：

        无baseline

            填充默认目录值，文件清单自动分析(扩展名限制)

        有baseline

            baseline目录值空：目录值仅继承，文件清单空

            baseline目录值非空：目录值仅继承，文件清单仅追加

降级目录

    组合包：目录仅继承，差异化文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，文件清单自动分析(扩展名限制)

        有baseline

            填充输入目录值，文件清单仅追加

    无输入值：

        无baseline

            填充默认目录值，文件清单自动分析(扩展名限制)

        有baseline

            baseline目录值空：目录值仅继承，文件清单空

            baseline目录值非空：目录值仅继承，文件清单仅追加

全量目录

    组合包：目录仅继承，文件清单仅继承

    有输入值：

        无baseline

            填充输入目录值，文件清单自动分析(扩展名限制)

        有baseline

            填充输入目录值，文件清单继承追加

    无输入值：

        无baseline

            填充默认目录值，文件清单自动分析(扩展名限制)

        有baseline

            baseline目录值空：填充默认目录值，文件清单自动分析(扩展名限制)

            baseline目录值非空：目录值仅继承，文件清单继承追加