package com.webank.plugins.artifacts.service;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import com.google.common.collect.ImmutableMap;
import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.commons.ApplicationProperties.CmdbDataProperties;
import com.webank.plugins.artifacts.dto.ConfigFileDto;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.CmdbServiceV2Stub;
import com.webank.plugins.artifacts.support.cmdb.StandardCmdbEntityRestClient;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbDiffConfigDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CiDataDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.s3.S3Client;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNodeDto;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNodeResultItemDto;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;
import com.webank.plugins.artifacts.support.saltstack.SaltstackServiceStub;

public abstract class AbstractArtifactService {
    private static final Logger log = LoggerFactory.getLogger(AbstractArtifactService.class);
    public static final String FILE_COMP_DELETED = "deleted";
    public static final String FILE_COMP_NEW = "new";
    public static final String FILE_COMP_CHANGED = "changed";
    public static final String FILE_COMP_SAME = "same";
    
    protected static final String CONSTANT_FIX_DATE = "fixed_date";
    protected static final String S3_KEY_DELIMITER = "_";
    protected static final String CONSTANT_CAT_CAT_TYPE = "cat.catType";
    protected static final String CONSTANT_INPUT_TYPE = "inputType";
    protected static final String CONSTANT_CI_TYPE = "ciType";
    
    

    @Autowired
    protected CmdbServiceV2Stub cmdbServiceV2Stub;

    @Autowired
    protected SaltstackServiceStub saltstackServiceStub;

    @Autowired
    protected CmdbDataProperties cmdbDataProperties;

    @Autowired
    protected ApplicationProperties applicationProperties;
    
    @Autowired
    protected StandardCmdbEntityRestClient standardCmdbEntityRestClient;
    
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
    
    public List<Object> savePackageToCmdb(File file, String unitDesignId, String uploadUser, String deployPackageUrl,
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
    
    protected void updatePackageCi(Map<String,Object> packageUpdateParamsMap){
        cmdbServiceV2Stub.updateCiData(cmdbDataProperties.getCiTypeIdOfPackage(), packageUpdateParamsMap);
    }
    
    protected String genMd5Value(File file) {
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
    
    @SuppressWarnings("rawtypes")
    protected String retrieveS3EndpointWithKeyByPackageId(String packageCiGuid) {
        Map pkg = retrievePackageCiByGuid(packageCiGuid);
        String s3Key = pkg.get("md5_value") + S3_KEY_DELIMITER + pkg.get("name");
        String endpointWithKey = applicationProperties.getArtifactsS3ServerUrl() + "/"
                + applicationProperties.getArtifactsS3BucketName() + "/" + s3Key;
        return endpointWithKey;
    }
    
    public String retrieveS3EndpointWithKeyByPackageCiMap(Map<String,Object> pkgCiMap) {
        String s3Key = pkgCiMap.get("md5_value") + S3_KEY_DELIMITER + pkgCiMap.get("name");
        String endpointWithKey = applicationProperties.getArtifactsS3ServerUrl() + "/"
                + applicationProperties.getArtifactsS3BucketName() + "/" + s3Key;
        return endpointWithKey;
    }
    
    @SuppressWarnings("unchecked")
    protected Map<String,Object> retrievePackageCiByGuid(String packageCiGuid){
        PaginationQuery queryObject = PaginationQuery.defaultQueryObject().addEqualsFilter("guid", packageCiGuid);
        PaginationQueryResult<Object> result = cmdbServiceV2Stub.queryCiData(cmdbDataProperties.getCiTypeIdOfPackage(),
                queryObject);
        if (result == null || result.getContents().isEmpty()) {
            throw new PluginException(String.format("Package with ID [%s] not found.", packageCiGuid)).withErrorCode("3008", packageCiGuid);
        }

        Map<String,Object> pkgData = (Map<String,Object>) result.getContents().get(0);
        Map<String,Object> pkg = (Map<String,Object>) pkgData.get("data");
        log.info("Got package data with guid {} {}", packageCiGuid, pkg);
        return pkg;
    }
    
    public List<SaltFileNodeDto> listFilesOfCurrentDirs(String currentDir, String endpoint) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputParamMaps = new ArrayList<Map<String, Object>>();
        Map<String, Object> inputParamMap = new HashMap<String, Object>();
        inputParamMap.put("endpoint", endpoint);
        inputParamMap.put("accessKey", applicationProperties.getArtifactsS3AccessKey());
        inputParamMap.put("secretKey", applicationProperties.getArtifactsS3SecretKey());
        inputParamMap.put("currentDir", currentDir);
        
        inputParamMaps.add(inputParamMap);
        request.setInputs(inputParamMaps);
        ResultData<SaltFileNodeResultItemDto> fileNodesResultItemData = saltstackServiceStub
                .getReleasedPackageFilesByCurrentDir(applicationProperties.getWecubeGatewayServerUrl(), request);
        
        List<SaltFileNodeResultItemDto> resultItemDtos = fileNodesResultItemData.getOutputs();
        if(resultItemDtos == null || resultItemDtos.isEmpty()) {
            return Collections.emptyList();
        }
        
        List<SaltFileNodeDto> fileNodes = resultItemDtos.get(0).getFiles();
        if(fileNodes == null) {
            return Collections.emptyList();
        }
        
        return fileNodes;
    }
    
    protected Boolean convertCmdbObjectToBoolean(Object obj) {
        if (obj == null) {
            return null;
        }

        if (obj instanceof Boolean) {
            return (Boolean) obj;
        }

        if (obj instanceof String) {
            if ("true".equalsIgnoreCase((String) obj)) {
                return true;
            } else {
                return false;
            }
        }

        return null;
    }
    
    @SuppressWarnings("unchecked")
    protected Set<String> getBoundDiffConfVarGuidsFromPackage(Map<String, Object> packageCiMap) {
        Set<String> guids = new HashSet<String>();

        List<Object> boundDiffConfVariables = (List<Object>) packageCiMap.get("diff_conf_variable");
        if (boundDiffConfVariables == null || boundDiffConfVariables.isEmpty()) {
            return guids;
        }

        for (Object obj : boundDiffConfVariables) {
            if (obj == null) {
                continue;
            }

            if (obj instanceof Map) {
                Map<String, Object> boundDiffMap = (Map<String, Object>) obj;
                guids.add((String) boundDiffMap.get("guid"));
            }

            if (obj instanceof String) {
                guids.add((String) obj);
            }
        }

        return guids;
    }

    @SuppressWarnings("unchecked")
    protected boolean verifyIfBoundToCurrentPackage(CmdbDiffConfigDto cmdbDiffConfig,
            List<Object> boundDiffConfVariables) {
        if (boundDiffConfVariables == null || boundDiffConfVariables.isEmpty()) {
            return false;
        }
        for (Object boundDiffConfVariable : boundDiffConfVariables) {
            String diffConfVarGuid = null;
            if (boundDiffConfVariable instanceof Map) {
                Map<String, Object> boundDiffConfVariableMap = (Map<String, Object>) boundDiffConfVariable;
                diffConfVarGuid = (String) boundDiffConfVariableMap.get("guid");
            } else {
                diffConfVarGuid = (String) boundDiffConfVariable;
            }
            if (diffConfVarGuid.equals(cmdbDiffConfig.getGuid())) {
                return true;
            }
        }
        return false;
    }
    
    @SuppressWarnings("unchecked")
    protected String getBaselinePackageGuidFromCiMap(Map<String, Object> packageCiMap) {
        Map<String, Object> baselinePackageCiMap = (Map<String, Object>) packageCiMap.get("baseline_package");
        if(baselinePackageCiMap == null) {
            return null;
        }
        
        String baselinePackageGuid = (String) baselinePackageCiMap.get("guid");

        return baselinePackageGuid;
    }
    
    
    protected String assembleFileItemsToString(List<ConfigFileDto> dtos) {
        if (dtos == null ) {
            return null;
        }
        
        if(dtos.isEmpty()) {
            return "";
        }
        
        String configFileStr = String.join("|", dtos.stream().map(dto -> {
            return dto.getFilename();
        }).collect(Collectors.toList()));

        return configFileStr;
    }
}
