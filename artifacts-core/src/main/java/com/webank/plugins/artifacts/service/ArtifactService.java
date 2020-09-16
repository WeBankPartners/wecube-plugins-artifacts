package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CatCodeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CategoryDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataTreeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeAttrDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.SpecialConnectorDtoResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.OperateCiDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.Dialect;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.Sorting;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;

@Service
public class ArtifactService extends AbstractArtifactService {
    private static final Logger log = LoggerFactory.getLogger(ArtifactService.class);

    public void deactive(String packageId) {
        updateState(packageId, cmdbDataProperties.getEnumCodeDestroyedOfCiStateOfCreate());
    }

    public void active(String packageId) {
        updateState(packageId, cmdbDataProperties.getEnumCodeChangeOfCiStateOfCreate());
    }

    public Object operateState(List<OperateCiDto> operateCiDtos, String operation) {
        return cmdbServiceV2Stub.operateCiForState(operateCiDtos, operation);
    }

    public Object getCurrentDirs(String packageId, String currentDir) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputParamMaps = new ArrayList<Map<String, Object>>();
        Map<String, Object> inputParamMap = new HashMap<String, Object>();
        inputParamMap.put("endpoint", retrieveS3EndpointWithKeyByPackageId(packageId));
        inputParamMap.put("accessKey", applicationProperties.getArtifactsS3AccessKey());
        inputParamMap.put("secretKey", applicationProperties.getArtifactsS3SecretKey());
        inputParamMap.put("currentDir", currentDir);
        
        inputParamMaps.add(inputParamMap);
        request.setInputs(inputParamMaps);
        return saltstackServiceStub
                .getReleasedPackageFilesByCurrentDir(applicationProperties.getWecubeGatewayServerUrl(), request);
    }

    public Object getPropertyKeys(String packageId, String filePath) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputParamMaps = new ArrayList<>();
        Map<String, Object> inputParamMap = new HashMap<String, Object>();
        inputParamMap.put("endpoint", retrieveS3EndpointWithKeyByPackageId(packageId));
        inputParamMap.put("accessKey", applicationProperties.getArtifactsS3AccessKey());
        inputParamMap.put("secretKey", applicationProperties.getArtifactsS3SecretKey());
        inputParamMap.put("filePath", filePath);
        
        inputParamMaps.add(inputParamMap);
        request.setInputs(inputParamMaps);
        return saltstackServiceStub
                .getReleasedPackagePropertyKeysByFilePath(applicationProperties.getWecubeGatewayServerUrl(), request);
    }

    public Object getArtifactSystemDesignTree(String systemDesignId) {
        List<CiDataTreeDto> tree = new ArrayList<>();
        PaginationQuery queryObject = new PaginationQuery();
        Dialect dialect = new Dialect();
        dialect.setShowCiHistory(true);
        queryObject.setDialect(dialect);
        queryObject.addEqualsFilter("guid", systemDesignId);
        PaginationQueryResult<Object> ciData = cmdbServiceV2Stub
                .queryCiData(cmdbDataProperties.getCiTypeIdOfSystemDesign(), queryObject);

        if (ciData == null || ciData.getContents() == null || ciData.getContents().isEmpty()) {
            throw new PluginException(String.format("Can not find ci data for guid [%s]", systemDesignId));
        }

        Object fixedDate = ((Map) ((Map) ciData.getContents().get(0)).get("data")).get(CONSTANT_FIX_DATE);
        if (fixedDate != null) {
            List<CiDataTreeDto> dtos = cmdbServiceV2Stub.getCiDataDetailForVersion(
                    cmdbDataProperties.getCiTypeIdOfSystemDesign(), cmdbDataProperties.getCiTypeIdOfUnitDesign(),
                    fixedDate.toString());

            dtos.forEach(dto -> {
                if (systemDesignId.equals(((Map) dto.getData()).get("guid"))) {
                    tree.add(dto);
                }
            });
        }
        return tree;
    }

    public PaginationQueryResult<Object> getSystemDesignVersions() {
        PaginationQueryResult<Object> queryResult = new PaginationQueryResult<>();

        PaginationQuery queryObject = new PaginationQuery();
        Dialect dialect = new Dialect();
        dialect.setShowCiHistory(true);
        queryObject.setDialect(dialect);
        queryObject.addNotNullFilter(CONSTANT_FIX_DATE);
        queryObject.addNotEqualsFilter(CONSTANT_FIX_DATE, "");
        queryObject.setSorting(new Sorting(false, CONSTANT_FIX_DATE));

        PaginationQueryResult<Object> ciDatas = cmdbServiceV2Stub
                .queryCiData(cmdbDataProperties.getCiTypeIdOfSystemDesign(), queryObject);

        queryResult.setContents(extractedLatestVersionSystemDesigns(ciDatas));

        return queryResult;
    }

    public void saveDiffConfigEnumCodes(CatCodeDto requestCode) {
        CategoryDto cat = cmdbServiceV2Stub.getEnumCategoryByName(cmdbDataProperties.getEnumCategoryNameOfDiffConf());
        if (cat == null) {
            String msg = String.format("Can not find category with name [%s].",
                    cmdbDataProperties.getEnumCategoryNameOfDiffConf());
            throw new PluginException("3005", msg, cmdbDataProperties.getEnumCategoryNameOfDiffConf());
        }

        CatCodeDto code = new CatCodeDto();
        code.setCatId(cat.getCatId());
        code.setCode(requestCode.getCode());
        code.setValue(requestCode.getValue());
        cmdbServiceV2Stub.createEnumCodes(code);
    }

    public List<CatCodeDto> getDiffConfigEnumCodes() {
        CategoryDto cat = cmdbServiceV2Stub.getEnumCategoryByName(cmdbDataProperties.getEnumCategoryNameOfDiffConf());
        if (cat == null) {
            String msg = String.format("Can not find category with name [%s].",
                    cmdbDataProperties.getEnumCategoryNameOfDiffConf());
            throw new PluginException("3005", msg, cmdbDataProperties.getEnumCategoryNameOfDiffConf());
        }
        return cmdbServiceV2Stub.getEnumCodesByCategoryId(cat.getCatId());
    }

    public List<CiTypeDto> getCiTypes(Boolean withAttributes, String status) {
        return cmdbServiceV2Stub.getAllCiTypes(withAttributes, status);
    }

    public PaginationQueryResult<CatCodeDto> querySystemEnumCodesWithRefResources(PaginationQuery queryObject) {
        queryObject.addEqualsFilter(CONSTANT_CAT_CAT_TYPE, cmdbDataProperties.getEnumCategoryTypeSystem());
        queryObject.addReferenceResource("cat");
        queryObject.addReferenceResource(CONSTANT_CAT_CAT_TYPE);
        return cmdbServiceV2Stub.queryEnumCodes(queryObject);
    }

    public void deleteCiData(int ciTypeId, List<String> ids) {
        cmdbServiceV2Stub.deleteCiData(ciTypeId, ids);

    }

    public List<CiTypeAttrDto> getCiTypeReferenceBy(Integer ciTypeId) {
        PaginationQuery queryObject = new PaginationQuery().addEqualsFilter("referenceId", ciTypeId)
                .addInFilter(CONSTANT_INPUT_TYPE, Arrays.asList("ref", "multiRef"))
                .addReferenceResource(CONSTANT_CI_TYPE);
        queryObject.addReferenceResource(CONSTANT_CI_TYPE);
        return cmdbServiceV2Stub.queryCiTypeAttributes(queryObject);
    }

    public List<SpecialConnectorDtoResponse> getSpecialConnector() {
        return cmdbServiceV2Stub.getSpecialConnector();
    }

    private List<Object> extractedLatestVersionSystemDesigns(PaginationQueryResult<Object> ciDatas) {
        List<Object> finalCiDatas = new ArrayList<>();
        ciDatas.getContents().forEach(ciData -> {
            if (ciData instanceof Map) {
                Map map = (Map) ciData;
                if (!isExist(finalCiDatas, map.get("data"))) {
                    finalCiDatas.add(ciData);
                }
            }
        });
        return finalCiDatas;
    }

    private boolean isExist(List<Object> results, Object systemName) {
        for (Object result : results) {
            Map m = (Map) result;
            Object existRguid = ((Map) m.get("data")).get("r_guid");
            Object newRguid = ((Map) systemName).get("r_guid");
            if (existRguid != null && existRguid.equals(newRguid)) {
                return true;
            }
        }
        return false;
    }

    private void updateState(String packageId, String operation) {
        List<OperateCiDto> operateCiDtos = new ArrayList<>();
        operateCiDtos.add(new OperateCiDto(packageId, cmdbDataProperties.getCiTypeIdOfPackage()));
        cmdbServiceV2Stub.operateCiForState(operateCiDtos, operation);
    }

}
