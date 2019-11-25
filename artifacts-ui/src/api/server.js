import { req as request, baseURL } from "./base";
let req = request;
if (window.request) {
  req = {
    post: (url, ...params) => window.request.post(baseURL + url, ...params),
    get: (url, ...params) => window.request.get(baseURL + url, ...params),
    delete: (url, ...params) => window.request.delete(baseURL + url, ...params),
    put: (url, ...params) => window.request.put(baseURL + url, ...params)
  };
}

// artifact manage
export const getPackageCiTypeId = () => req.get("/getPackageCiTypeId");
export const getAllCITypesByLayerWithAttr = data => {
  const status = data.toString();
  return req.get(
    `/ci-types?group-by=layer&with-attributes=yes&status=${status}`
  );
};
export const getSystemDesignVersions = () => {
  return req.get(`/system-design-versions`);
};
export const getSystemDesignVersion = version => {
  return req.get(`/system-design-versions/${version}`);
};
export const queryPackages = (guid, data) => {
  return req.post(`/unit-designs/${guid}/packages/query`, data);
};
export const deleteCiDatas = data => {
  return req.post(
    `/ci-types/${data.id}/ci-data/batch-delete`,
    data.deleteData
  );
};
export const operateCiState = (ciTypeId, guid, op) => {
  const payload = [{ ciTypeId, guid }];
  return req.post(`/ci/state/operate?operation=${op}`, payload);
};
export const getFiles = (guid, packageId, data) => {
  return req.post(
    `/unit-designs/${guid}/packages/${packageId}/files/query`,
    data
  );
};
export const getKeys = (guid, packageId, data) => {
  return req.post(
    `/unit-designs/${guid}/packages/${packageId}/property-keys/query`,
    data
  );
};
export const saveConfigFiles = (guid, packageId, data) => {
  return req.post(
    `/unit-designs/${guid}/packages/${packageId}/save`,
    data
  );
};
export const saveDiffConfigEnumCodes = data =>
  req.post("/enum/codes/diff-config/save", data);
export const getDiffConfigEnumCodes = () =>
  req.get("/enum/codes/diff-config/query");
export const getAllSystemEnumCodes = data => {
  return req.post(`/enum/system/codes`, data);
};
