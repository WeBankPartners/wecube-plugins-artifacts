package com.webank.plugins.artifacts.service;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Map;

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONException;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.web.util.UriComponentsBuilder;

import com.google.common.collect.ImmutableMap;
import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.commons.ApplicationProperties.CmdbDataProperties;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.dto.ConfigKeyInfoDto;
import com.webank.plugins.artifacts.dto.DeployConfigFileDto;
import com.webank.plugins.artifacts.dto.DeployPackageConfigDto;
import com.webank.plugins.artifacts.dto.PackageDto;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.CmdbServiceV2Stub;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CatCodeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CategoryDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataTreeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeAttrDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiTypeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CmdbResponses.SpecialConnectorDtoResponse;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.OperateCiDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.Dialect;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.Sorting;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.nexus.NexusAssetItemInfo;
import com.webank.plugins.artifacts.support.nexus.NexusClient;
import com.webank.plugins.artifacts.support.nexus.NexusDirectiryDto;
import com.webank.plugins.artifacts.support.nexus.NexusSearchAssetResponse;
import com.webank.plugins.artifacts.support.s3.S3Client;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigFileDto;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigKeyInfoDto;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;
import com.webank.plugins.artifacts.support.saltstack.SaltstackServiceStub;

@Service
public class ArtifactService {
    private static final Logger log = LoggerFactory.getLogger(ArtifactService.class);
    private static final String CONSTANT_FIX_DATE = "fixed_date";
    private static final String S3_KEY_DELIMITER = "_";
    private static final String CONSTANT_CAT_CAT_TYPE = "cat.catType";
    private static final String CONSTANT_INPUT_TYPE = "inputType";
    private static final String CONSTANT_CI_TYPE = "ciType";

    private static final String NEXUS_SEARCH_ASSET_API_PATH = "/service/rest/beta/search/assets";

    @Autowired
    private CmdbServiceV2Stub cmdbServiceV2Stub;

    @Autowired
    private SaltstackServiceStub saltstackServiceStub;

    @Autowired
    CmdbDataProperties cmdbDataProperties;

    @Autowired
    private ApplicationProperties applicationProperties;

    @Autowired
    private NexusClient nexusClient;

    public String uploadPackageToS3(File file) {
        if (file == null) {
            throw new PluginException("Upload package file is required.");
        }

        String s3Key = genMd5Value(file) + S3_KEY_DELIMITER + file.getName();
        String url = new S3Client(applicationProperties.getArtifactsS3ServerUrl(),
                applicationProperties.getArtifactsS3AccessKey(), applicationProperties.getArtifactsS3SecretKey())
                        .uploadFile(applicationProperties.getArtifactsS3BucketName(), s3Key, file);
        return url.substring(0, url.indexOf("?"));
    }

    public List<CiDataDto> savePackageToCmdb(File file, String unitDesignId, String uploadUser, String deployPackageUrl,
            String authorization) {
        Map<String, Object> pkg = ImmutableMap.<String, Object>builder().put("name", file.getName())
                .put("deploy_package_url", deployPackageUrl).put("md5_value", genMd5Value(file))
                .put("description", file.getName()).put("upload_user", uploadUser)
                .put("upload_time", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()))
                .put("unit_design", unitDesignId).build();

        if (StringUtils.isNoneBlank(authorization)) {
            AuthorizationStorage.getIntance().set(authorization);
        }
        return cmdbServiceV2Stub.createCiData(cmdbDataProperties.getCiTypeIdOfPackage(), pkg);
    }

    public void deactive(String packageId) {
        updateState(packageId, cmdbDataProperties.getEnumCodeDestroyedOfCiStateOfCreate());
    }

    public void active(String packageId) {
        updateState(packageId, cmdbDataProperties.getEnumCodeChangeOfCiStateOfCreate());
    }

    public Object operateState(List<OperateCiDto> operateCiDtos, String operation) {
        return cmdbServiceV2Stub.operateCiForState(operateCiDtos, operation);
    }

    public DeployPackageConfigDto saveConfigFiles(String unitDesignId, String packageId, PackageDto packageDto) {
        String files = String.join("|", packageDto.getConfigFilesWithPath());
        Map<String, Object> pkg = ImmutableMap.<String, Object>builder().put("guid", packageId)
                .put("deploy_file_path", packageDto.getDeployFile())
                .put("start_file_path", packageDto.getStartFile()).put("stop_file_path", packageDto.getStopFile())
                .put("diff_conf_file", files).put("is_decompression", packageDto.getIsDecompression()).build();
        cmdbServiceV2Stub.updateCiData(cmdbDataProperties.getCiTypeIdOfPackage(), pkg);
        
        
        //TODO
        DeployPackageConfigDto result = new DeployPackageConfigDto();
        result.setPackageId(packageId);
        result.setUnitDesignId(unitDesignId);
        
        //query keys by file
        for(String filePath : packageDto.getConfigFilesWithPath()){
            log.info("cal filepath:{}", filePath);
            calculatePropertyKeys(packageId, filePath);
        }
        
        //get diff guid from cmdb
        
        //create new diff if not exists
        
        
        return result;
    }
    
    public DeployConfigFileDto calculatePropertyKeys(String packageId, String filePath) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputs = new ArrayList<>();
        inputs.add(ImmutableMap.<String, Object>builder()
                .put("endpoint", retrieveS3EndpointWithKeyByPackageId(packageId))
                .put("accessKey", applicationProperties.getArtifactsS3AccessKey())
                .put("secretKey", applicationProperties.getArtifactsS3SecretKey()).put("filePath", filePath).build());
        request.setInputs(inputs);
        ResultData<SaltConfigFileDto> resultData = saltstackServiceStub
                .getReleasedPackagePropertyKeysByFilePath(applicationProperties.getWecubeGatewayServerUrl(), request);
        
        DeployConfigFileDto configFileDto = new DeployConfigFileDto();
        configFileDto.setFilePath(filePath);
        List<SaltConfigFileDto> saltConfigFileDtos = resultData.getOutputs();
        if(saltConfigFileDtos == null || saltConfigFileDtos.isEmpty()){
            return configFileDto;
        }
        
        log.info("SaltConfigFileDto size:{}", saltConfigFileDtos.size());
        SaltConfigFileDto saltConfigFileDto = saltConfigFileDtos.get(0);
        
        List<SaltConfigKeyInfoDto> saltConfigKeyInfos = saltConfigFileDto.getConfigKeyInfos();
        if(saltConfigKeyInfos == null || saltConfigKeyInfos.isEmpty()){
            return configFileDto;
        }
        
        for(SaltConfigKeyInfoDto saltConfigKeyInfo : saltConfigKeyInfos){
            log.info("saltConfigKeyInfo");
            ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
            configKeyInfo.setLine(saltConfigKeyInfo.getLine());
            configKeyInfo.setKey(saltConfigKeyInfo.getKey());
            configKeyInfo.setType(saltConfigKeyInfo.getType());
            
            configFileDto.addConfigKeyInfo(configKeyInfo);
        }
        
        return configFileDto;
    }

    public Object getCurrentDirs(String packageId, String currentDir) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputs = new ArrayList<>();
        inputs.add(
                ImmutableMap.<String, Object>builder().put("endpoint", retrieveS3EndpointWithKeyByPackageId(packageId))
                        .put("accessKey", applicationProperties.getArtifactsS3AccessKey())
                        .put("secretKey", applicationProperties.getArtifactsS3SecretKey()).put("currentDir", currentDir)
                        .build());
        request.setInputs(inputs);
        return saltstackServiceStub
                .getReleasedPackageFilesByCurrentDir(applicationProperties.getWecubeGatewayServerUrl(), request);
    }

    public Object getPropertyKeys(String packageId, String filePath) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputs = new ArrayList<>();
        inputs.add(ImmutableMap.<String, Object>builder()
                .put("endpoint", retrieveS3EndpointWithKeyByPackageId(packageId))
                .put("accessKey", applicationProperties.getArtifactsS3AccessKey())
                .put("secretKey", applicationProperties.getArtifactsS3SecretKey()).put("filePath", filePath).build());
        request.setInputs(inputs);
        return saltstackServiceStub
                .getReleasedPackagePropertyKeysByFilePath(applicationProperties.getWecubeGatewayServerUrl(), request);
    }

    private String retrieveS3EndpointWithKeyByPackageId(String packageId) {
        PaginationQuery queryObject = PaginationQuery.defaultQueryObject().addEqualsFilter("guid", packageId);
        PaginationQueryResult<Object> result = cmdbServiceV2Stub.queryCiData(cmdbDataProperties.getCiTypeIdOfPackage(),
                queryObject);
        if (result == null || result.getContents().isEmpty()) {
            throw new PluginException(String.format("Package with ID [%s] not found.", packageId));
        }

        Map pkgData = (Map) result.getContents().get(0);
        Map pkg = (Map) pkgData.get("data");
        String s3Key = pkg.get("md5_value") + S3_KEY_DELIMITER + pkg.get("name");
        String endpointWithKey = applicationProperties.getArtifactsS3ServerUrl() + "/"
                + applicationProperties.getArtifactsS3BucketName() + "/" + s3Key;
        return endpointWithKey;
    }

    private void updateState(String packageId, String operation) {
        List<OperateCiDto> operateCiDtos = new ArrayList<>();
        operateCiDtos.add(new OperateCiDto(packageId, cmdbDataProperties.getCiTypeIdOfPackage()));
        cmdbServiceV2Stub.operateCiForState(operateCiDtos, operation);
    }

    private String genMd5Value(File file) {
        if (file == null) {
            return null;
        }

        String md5Value = null;

        try {
            md5Value = DigestUtils.md5Hex(FileUtils.readFileToByteArray(file));
        } catch (Exception e) {
            String msg = String.format("Failed to generateMd5 value for file [%s].", file.getName());
            log.error(msg, e);
            throw new PluginException("3004", msg, file.getName());
        }
        return md5Value;
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

    public String getArtifactPath(String unitDesignId, PaginationQuery queryObject) {
        if (StringUtils.isBlank(unitDesignId)) {
            throw new PluginException("Unit design ID cannot be blank.");
        }
        String artifactPath = null;
        queryObject.addEqualsFilter("guid", unitDesignId);
        PaginationQueryResult<Object> objectPaginationQueryResult = cmdbServiceV2Stub
                .queryCiData(cmdbDataProperties.getCiTypeIdOfUnitDesign(), queryObject);

        if (objectPaginationQueryResult == null || objectPaginationQueryResult.getContents() == null
                || objectPaginationQueryResult.getContents().size() <= 0) {
            return artifactPath;
        }
        try {
            Map<String, String> ResultMap = (Map) objectPaginationQueryResult.getContents().get(0);
            JSONObject responseJson = (JSONObject) JSONObject.wrap(ResultMap.get("data"));
            // JSONObject unit_design =
            // responseJson.getJSONObject(applicationProperties.getCmdbArtifactPath());
            artifactPath = responseJson.getString(applicationProperties.getCmdbArtifactPath());
        } catch (JSONException e) {
            log.error("Can not parse CMDB Response json", e);
            throw new PluginException("3006","Cannot find Nexus path from CMDB.Please configure Nexus path in CMDB.");
        }
        return artifactPath;
    }

    public List<NexusDirectiryDto> queryNexusDirectory(String artifactPath) {
        if (artifactPath == null || artifactPath.isEmpty()) {
            throw new PluginException("Upload artifact path is required.");
        }

        // configuration parameters
        // String filter = "jar,zip";

        String nexusBaseUrl = applicationProperties.getArtifactsNexusServerUrl();
        String nexusRepository = applicationProperties.getArtifactsNexusRepository();
        String nexusSearchAssetApiUrl = nexusBaseUrl + NEXUS_SEARCH_ASSET_API_PATH;
        UriComponentsBuilder b = UriComponentsBuilder.fromHttpUrl(nexusSearchAssetApiUrl);
        b = b.queryParam("repository", nexusRepository);
        String group = null;
        if (StringUtils.isNoneBlank(artifactPath)) {
            group = artifactPath;
            if (!artifactPath.startsWith("/")) {
                group = "/" + group;
            }

            b = b.queryParam("group", group);
        }

        List<NexusDirectiryDto> results = new ArrayList<>();
        NexusSearchAssetResponse nexusSearchAssetResponse = nexusClient.searchAsset(b.build().toUri(),
                applicationProperties.getArtifactsNexusUsername(), applicationProperties.getArtifactsNexusPassword());

        String continuationToken = nexusSearchAssetResponse.getContinuationToken();
        List<NexusAssetItemInfo> assetItems = nexusSearchAssetResponse.getItems();
        for (NexusAssetItemInfo assetItem : assetItems) {
            if (assetItem.getPath().endsWith("jar") || assetItem.getPath().endsWith("zip")
                    || assetItem.getPath().endsWith("tar") || assetItem.getPath().endsWith("gz")
                    || assetItem.getPath().endsWith("tgz")) {
                NexusDirectiryDto directiryDto = new NexusDirectiryDto();
                directiryDto.setDownloadUrl(assetItem.getDownloadUrl());
                directiryDto
                        .setName(assetItem.getDownloadUrl().substring(assetItem.getDownloadUrl().lastIndexOf("/") + 1));
                results.add(directiryDto);
            }
        }

        while (StringUtils.isNoneBlank(continuationToken)) {
            b = UriComponentsBuilder.fromHttpUrl(nexusSearchAssetApiUrl);
            b = b.queryParam("repository", nexusRepository);
            if(StringUtils.isNoneBlank(group)){
                b = b.queryParam("group", group);
            }
            b = b.queryParam("continuationToken", continuationToken);

            nexusSearchAssetResponse = nexusClient.searchAsset(b.build().toUri(),
                    applicationProperties.getArtifactsNexusUsername(),
                    applicationProperties.getArtifactsNexusPassword());

            List<NexusAssetItemInfo> queryAssetItems = nexusSearchAssetResponse.getItems();
            for (NexusAssetItemInfo assetItem : queryAssetItems) {
                if (assetItem.getPath().endsWith("jar") || assetItem.getPath().endsWith("zip")) {
                    NexusDirectiryDto directiryDto = new NexusDirectiryDto();
                    directiryDto.setDownloadUrl(assetItem.getDownloadUrl());
                    directiryDto.setName(
                            assetItem.getDownloadUrl().substring(assetItem.getDownloadUrl().lastIndexOf("/") + 1));
                    results.add(directiryDto);
                }
            }

            continuationToken = nexusSearchAssetResponse.getContinuationToken();
        }
        return results;

    }

}
