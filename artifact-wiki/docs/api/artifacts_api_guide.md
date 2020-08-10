# Artifact API  
提供统一接口定义，为使用者提供清晰明了的使用方法


## API 常规操作 (CRUD):
- 新增 (Create)， 新增一个或多个资源  
- 查询 (Retrieve)，查询一个或多个资源，可自定义过滤及排序条件
- 更新 (Update)， 更新一个或多个资源  
- 删除 (Delete)， 删除一个或多个资源  


## API 概览及实例：  

#### [GET]/ci-types
查询CI类型
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
request|[QueryRequest](#QueryRequest)|否|请求参数对象

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```
{
  "groupBy": "groupBy",
  "status": "status",
  "with-attributes": "with-attributes"
}
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET]/ci-types/{ci-type-id}/attributes
查询CI配置
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
ci-type-id|String|否|CI类型ID

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI配置对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```
[
    "ci-type-id":"123456",
    "accept-input-types": 47
]
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```


#### [POST]/ci-types/{ci-type-id}/ci-data/batch-delete
批量删除CI-data
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
ci-type-id|String|否|CI类型ID

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI配置对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```
{
    “ciTypeId”:“1233”,
    "ciDataIds":{"1222","122","1222222"}
}
```
正常输出：
```
{
  "statusCode": "OK",
  "data": "Success"
}
```


#### [GET] /ci-types/{ci-type-id}/references/by
根据ciTypeId获取ciData
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:-- 
ci-type-id|String|否|CI类型ID

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI配置对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```
{
    “ciTypeId”:“1233”,
}
```
正常输出：
```
{
  "statusCode": "OK",
  "data": "Success"
}
```

#### [POST]/ci/state/operate
CI状态操作
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
operation|String|否|操作状态
ciIds|List|是|操作IDs

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI配置对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```
[
  {
    "ciTypeId": 0,
    "guid": "string"
  }
]
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET]/enum/codes/diff-config/query
查询不同的配置信息
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
Array|Array of [EnumCatDto](#EnumCatDto)|否|配置信息实体

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|CI配置对象
message|String|处理结果
status|String|处理状态

##### 示例：
正常输入：
```

```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST]/enum/codes/diff-config/save
保存枚举配置信息
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
request|[QueryRequest](#QueryRequest)|否|请求参数对象

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|枚举配置对象
message|String|处理结果
status|String|处理状态

正常输入：
```
{
  "callbackId": "string",
  "cat": {
    "callbackId": "string",
    "catId": 0,
    "catName": "string",
    "catType": {
      "callbackId": "string",
      "catTypeId": 0,
      "catTypeName": "string",
      "cats": [
        null
      ],
      "ciTypeId": 0,
      "description": "string",
      "errorMessage": "string"
    },
    "catTypeId": 0,
    "codes": [
      null
    ],
    "description": "string",
    "errorMessage": "string",
    "groupTypeId": 0
  },
  "catId": 0,
  "ciTypes": [
    {
      "attributes": [
        {
          "autoFillRule": "string",
          "callbackId": "string",
          "ciTypeAttrId": 0,
          "ciTypeId": 0,
          "description": "string",
          "displaySeqNo": 0,
          "errorMessage": "string",
          "filterRule": "string",
          "inputType": "string",
          "isAccessControlled": true,
          "isAuto": true,
          "isDefunct": true,
          "isDisplayed": true,
          "isEditable": true,
          "isHidden": true,
          "isNullable": true,
          "isRefreshable": true,
          "isSystem": true,
          "isUnique": true,
          "length": 0,
          "name": "string",
          "propertyName": "string",
          "propertyType": "string",
          "referenceId": 0,
          "referenceName": "string",
          "referenceType": 0,
          "searchSeqNo": 0,
          "specialLogic": "string",
          "status": "string"
        }
      ],
      "callbackId": "string",
      "catalogId": 0,
      "ciGlobalUniqueId": 0,
      "ciTypeId": 0,
      "description": "string",
      "errorMessage": "string",
      "imageFileId": 0,
      "layerId": 0,
      "name": "string",
      "seqNo": 0,
      "status": "string",
      "tableName": "string",
      "tenementId": 0,
      "zoomLevelId": 0
    }
  ],
  "code": "string",
  "codeDescription": "string",
  "codeId": 0,
  "errorMessage": "string",
  "groupCodeId": {},
  "groupName": "string",
  "seqNo": 0,
  "status": "string",
  "value": "string"
}
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /enum/system/codes
新增枚举名称/值
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:-- 
request|[QueryRequest](#QueryRequest)|否|请求参数对象

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|枚举配置对象
message|String|处理结果
status|String|处理状态

正常输入：
```
{
  "dialect": {
    "data": {},
    "showCiHistory": true
  },
  "filterRs": "string",
  "filters": [
    {
      "name": "string",
      "operator": "string",
      "value": {}
    }
  ],
  "filtersRelationship": "string",
  "groupBys": [
    "string"
  ],
  "pageable": {
    "pageSize": 0,
    "startIndex": 0
  },
  "paging": true,
  "refResources": [
    "string"
  ],
  "resultColumns": [
    "string"
  ],
  "sorting": {
    "asc": true,
    "field": "string"
  }
}
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET]/getPackageCiTypeId
根据CiTypeId获取package
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Integer|CIType类型
message|String|处理结果
status|String|处理状态
正常输入：
```
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET]/static-data/special-connector
获取特殊的连接
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Integer|CIType类型
message|String|处理结果
status|String|处理状态
正常输入：
```
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET]/system-design-versions
获取系统版本
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|系统设计版本
message|String|处理结果
status|String|处理状态
正常输入：
```
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [GET] /system-design-versions/{system-design-id}
新增配置项类型
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:-- 
system-design-id|String|是|系统设计id

##### 输出参数：
参数名称|类型|描述
:--|:--|:--  
data|Object|系统设计版本
message|String|处理结果
status|String|处理状态

正常输入：
```
{
    "system-design-id":"12332"
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/{package-id}/active
激活配置项
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
unit-design-id|String|是|单元设计id
package-id|String|是|packageId

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|系统设计版本
message|String|处理结果
status|String|处理状态

正常输入：
```
{
    "unit-design-id":"12332"；
    "package-id":"123212"；
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/{package-id}/deactive
注销配置项
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
unit-design-id|String|是|单元设计id
package-id|String|是|packageId

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|系统设计版本
message|String|处理结果
status|String|处理状态

正常输入：
```
{
    "unit-design-id":"12332"；
    "package-id":"123212"；
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/{package-id}/files/query
查询当前包测试版本
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
unit-design-id|String|是|单元设计id
package-id|String|是|packageId
additionalProperties|Map|是|查询参数

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|单元设计实体
message|String|处理结果
status|String|处理状态

正常输入：
```
{
    "package-id":"123212"；
    "additionalProperties":[
                               "string"
                             ]
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/{package-id}/property-keys/query
查询单元设计
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:-- 
unit-design-id|String|是|单元设计id
package-id|String|是|packageId
additionalProperties|Map|是|查询参数

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|单元设计实体
message|String|处理结果
status|String|处理状态

正常输入：
```
{
    "package-id":"123212"；
    "additionalProperties":[
                               "string"
                             ]
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/{package-id}/save
保存单元设计项
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
PackageDomain|[PackageDomain](#PackageDomain)|否|请求参数对象

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|单元设计实体
message|String|处理结果
status|String|处理状态
正常输入：
```
{
  "configFilesWithPath": [
    "string"
  ],
  "deployFile": "string",
  "isDecompression": "string",
  "startFile": "string",
  "stopFile": "string"
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/query
查询单元设计package
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
queryObject| [PaginationQuery](#PaginationQuery)|是|查询参数

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|单元设计实体
message|String|处理结果
status|String|处理状态

正常输入：
```
{
  "dialect": {
    "data": {},
    "showCiHistory": true
  },
  "filterRs": "string",
  "filters": [
    {
      "name": "string",
      "operator": "string",
      "value": {}
    }
  ],
  "filtersRelationship": "string",
  "groupBys": [
    "string"
  ],
  "pageable": {
    "pageSize": 0,
    "startIndex": 0
  },
  "paging": true,
  "refResources": [
    "string"
  ],
  "resultColumns": [
    "string"
  ],
  "sorting": {
    "asc": true,
    "field": "string"
  }
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/queryNexusDirectiry
删除配置项类型属性
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
unit-design-id|String|是|单元设计ID

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|neuxs包目录
message|String|处理结果
status|String|处理状态
正常输入：
```
{
  "dialect": {
    "data": {},
    "showCiHistory": true
  },
  "filterRs": "string",
  "filters": [
    {
      "name": "string",
      "operator": "string",
      "value": {}
    }
  ],
  "filtersRelationship": "string",
  "groupBys": [
    "string"
  ],
  "pageable": {
    "pageSize": 0,
    "startIndex": 0
  },
  "paging": true,
  "refResources": [
    "string"
  ],
  "resultColumns": [
    "string"
  ],
  "sorting": {
    "asc": true,
    "field": "string"
  }
}
```

正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```


#### [POST] /unit-designs/{unit-design-id}/packages/upload
上传物料包
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:-- 
unit-design-id|String|是|单元设计ID
file|File|是|待上传文件.

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|保存成功CI单元对象
message|String|处理结果
status|String|处理状态

正常输入：
```
{
  "file": file,
  "unit-design-id": "788"
}
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```

#### [POST] /unit-designs/{unit-design-id}/packages/uploadNexusPackage
上传nexus包到S3仓库
##### 输入参数：
参数名称|类型|必选|描述
:--|:--|:--|:--
unit-design-id|String|是|单元设计ID
downloadUrl|String|是|nexus保存包路径

##### 输出参数：
参数名称|类型|描述
:--|:--|:--    
data|Object|保存成功CI单元对象
message|String|处理结果
status|String|处理状态
正常输入：
```
{
  "downloadUrl": "http://127.0.0.1:8080/nexus/...",
  "unit-design-id": "788"
}
```
正常输出：
```
{
  "data": {},
  "message": "string",
  "status": "string"
}
```
