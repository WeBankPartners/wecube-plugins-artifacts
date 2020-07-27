import { req as request, baseURL } from './base'
import { pluginErrorMessage } from './base-plugin'
let req = request
if (window.request) {
  req = {
    post: (url, ...params) => pluginErrorMessage(window.request.post(baseURL + url, ...params)),
    get: (url, ...params) => pluginErrorMessage(window.request.get(baseURL + url, ...params)),
    delete: (url, ...params) => pluginErrorMessage(window.request.delete(baseURL + url, ...params)),
    put: (url, ...params) => pluginErrorMessage(window.request.put(baseURL + url, ...params))
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
export const deleteCiDatas = data => req.post(`/ci-types/${data.id}/ci-data/batch-delete`, data.deleteData)
export const operateCiState = (ciTypeId, guid, op) => {
  const payload = [{ ciTypeId, guid }]
  return req.post(`/ci/state/operate?operation=${op}`, payload)
}
export const getFiles = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/files/query`, data)
export const getKeys = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/property-keys/query`, data)
export const saveConfigFiles = (guid, packageId, data) => req.post(`/unit-designs/${guid}/packages/${packageId}/save`, data)
export const retrieveEntity = (packageName, entityName) => req.get(`/platform/v1/packages/${packageName}/entities/${entityName}/retrieve`)
export const createEntity = (packageName, entityName, data) => req.post(`/platform/v1/packages/${packageName}/entities/${entityName}/create`, data)
export const updateEntity = (packageName, entityName, data) => req.post(`/platform/v1/packages/${packageName}/entities/${entityName}/update`, data)
export const getAllSystemEnumCodes = data => req.post(`/enum/system/codes`, data)
export const getRefCiTypeFrom = id => req.get(`/ci-types/${id}/references/by`)
export const getCiTypeAttr = id => req.get(`/ci-types/${id}/attributes`)
export const getSpecialConnector = () => req.get('/static-data/special-connector')
export const queryArtifactsList = (guid, data) => req.post(`/unit-designs/${guid}/packages/queryNexusDirectiry`, data)
export const uploadArtifact = (guid, url) => req.post(`/unit-designs/${guid}/packages/uploadNexusPackage?downloadUrl=${url}`)
