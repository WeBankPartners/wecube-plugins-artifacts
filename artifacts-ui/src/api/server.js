import { req as request, baseURL } from './base'
import { pluginErrorMessage } from './base-plugin'
let req = request
if (window.request) {
  req = {
    post: (url, ...params) => pluginErrorMessage(window.request.post(baseURL + url, ...params)),
    get: (url, ...params) => pluginErrorMessage(window.request.get(baseURL + url, ...params)),
    delete: (url, ...params) => pluginErrorMessage(window.request.delete(baseURL + url, ...params)),
    put: (url, ...params) => pluginErrorMessage(window.request.put(baseURL + url, ...params)),
    patch: (url, ...params) => pluginErrorMessage(window.request.patch(baseURL + url, ...params))
  }
}

// artifact manage
export const getPackageCiTypeId = () => req.get('/getPackageCiTypeId')
export const getAllCITypesWithAttr = data => {
  const status = data.toString()
  return req.get(`/ci-types?with-attributes=yes&status=${status}`)
}
export const getSystemDesignVersions = () => req.get(`/system-design-versions`)
export const getSystemDesignVersion = version => req.get(`/system-design-versions/${version}`)
export const queryPackages = (guid, data) => req.post(`/unit-designs/${guid}/packages/query`, data)
export const queryHistoryPackages = packageId => req.get(`/packages/${packageId}/history`)
export const getPackageDetail = (guid, packageId) => req.get(`/unit-designs/${guid}/packages/${packageId}/query`)
export const deleteCiDatas = data => req.post(`/ci-types/${data.id}/ci-data/batch-delete`, data.deleteData)
export const operateCiState = (ciTypeId, guid, op) => {
  const payload = [{ ciTypeId, guid }]
  return req.post(`/ci/state/operate?operation=${op}`, payload)
}
export const operateCiStateWithData = (ciTypeId, data, op) => {
  const payload = [{ ciTypeId: ciTypeId, ...data }]
  return req.post(`/ci/state/operate?operation=${op}`, payload)
}
export const getFiles = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/files/query`, data)
export const compareBaseLineFiles = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/comparison`, data)
export const updatePackage = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/update`, data)
export const getKeys = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/property-keys/query`, data)
export const saveConfigFiles = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/save`, data)
// export const retrieveEntity = (packageName, entityName) => req.get(`/platform/v1/packages/${packageName}/entities/${entityName}/retrieve`)
export const createEntity = (packageName, entityName, data) => req.post(`/platform/v1/packages/${packageName}/entities/${entityName}/create`, data)
export const updateEntity = (packageName, entityName, data) => req.post(`/platform/v1/packages/${packageName}/entities/${entityName}/update`, data)
export const getAllSystemEnumCodes = catId => req.get(`/enum/system/codes/${catId}`)
export const getCITypeOperations = ciTypeId => req.get(`/ci-types/${ciTypeId}/operations`)
export const getRefCiTypeFrom = id => req.get(`/ci-types/${id}/references/by`)
export const getCiTypeAttr = id => req.get(`/ci-types/${id}/attributes`)
export const getSpecialConnector = () => req.get('/static-data/special-connector')
export const getVariableRootCiTypeId = () => req.get('/getVariableRootCiTypeId')
export const getEntitiesByCiType = (packageName, ci, data) => req.post(`/platform/v1/packages/${packageName}/entities/${ci}/retrieve`, data)
// 获取cmdb中差异化变量
export const getDiffVariable = (citype, data) => req.post(`/cidata/${citype}/query`, data)

export const queryArtifactsList = (guid, data) => req.post(`/unit-designs/${guid}/packages/queryNexusDirectiry`, data)
export const uploadArtifact = (guid, url, baselinePackage, packageType) => req.post(`/unit-designs/${guid}/packages/uploadNexusPackage?downloadUrl=${url}&baseline_package=${encodeURIComponent(baselinePackage)}&package_type=${encodeURIComponent(packageType)}`)

export const uploadLocalArtifact = (guid, formData) => req.post(`/unit-designs/${guid}/packages/upload`, formData)

export const getCompareContent = (unitDesignId, deployPackageId, data) => req.post(`/unit-designs/${unitDesignId}/packages/${deployPackageId}/files/comparison`, data)

export const pushPkg = (unitDesignId, deployPackageId) => req.post(`/unit-designs/${unitDesignId}/packages/${deployPackageId}/push`)

// 获取上传路径
export const getFilePath = guid => req.get(`/unit-designs/${guid}/packages/queryNexusPath`)
// 获取按钮权限
export const sysConfig = () => req.get(`/sysconfig`)
// 获取可用编排
export const getFlowLists = guid => req.get(`/process/definitions?rootEntityGuid=${guid}`)
// 获取各包类型下数据的数量
export const getPkgTypeNum = unitDesignId => req.post(`/unit-designs/${unitDesignId}/packages/statistics`, {})

export const getUserList = guid => req.get(`/users`)
// 获取所有角色
export const getRoleList = params => req.get('/platform/v1/roles/retrieve', { params })
// 获取当前用户角色
export const getCurrentUserRoles = () => req.get('/platform/v1/users/roles')
// 保存模版
export const saveTemplate = data => req.post(`/api/v1/diff-conf-templates`, data)
export const updateTemplate = (data, id) => req.patch(`/api/v1/diff-conf-templates/${id}`, data)

// 获取模版列表
export const getTemplate = queryString => req.get(`/api/v1/diff-conf-templates?${queryString}`)
export const deleteTemplate = id => req.delete(`/api/v1/diff-conf-templates/${id}`)
// 获取差异化变量试算结果
export const getVariableValue = data => req.post(`/app-instances/variable-values`, data)
// 获取待试算实例
export const getCalcInstance = data => req.post(`/unit-designs/app-instances`, data)
