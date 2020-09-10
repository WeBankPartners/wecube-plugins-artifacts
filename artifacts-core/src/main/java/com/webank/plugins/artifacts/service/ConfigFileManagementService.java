package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.google.common.collect.ImmutableMap;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.dto.ConfigFileDto;
import com.webank.plugins.artifacts.dto.ConfigKeyInfoDto;
import com.webank.plugins.artifacts.dto.ConfigPackageDto;
import com.webank.plugins.artifacts.dto.PackageComparisionRequestDto;
import com.webank.plugins.artifacts.dto.PackageComparisionResultDto;
import com.webank.plugins.artifacts.dto.PackageDto;
import com.webank.plugins.artifacts.dto.SinglePackageQueryResultDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigFileDto;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigKeyInfoDto;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;

@Service
public class ConfigFileManagementService extends AbstractArtifactService{
    private static final Logger log = LoggerFactory.getLogger(ConfigFileManagementService.class);
    
    public PackageComparisionResultDto packageComparision(String unitDesignId, String packageId, PackageComparisionRequestDto comparisonReqDto){
        //TODO
        
        return null;
    }
    
    public SinglePackageQueryResultDto querySinglePackage(String unitDesignId, String packageId){
        Map<String,Object> currPackageCiMap = retrievePackageCiByGuid(packageId);
        log.info("currPackageCi:{}", currPackageCiMap);
        log.info("baseline_package:{}", currPackageCiMap.get("baseline_package"));
        String baselinePackageGuid = (String) currPackageCiMap.get("baseline_package");
        Map<String,Object> baselinePackageCiMap = null;
        if(StringUtils.isNoneBlank(baselinePackageGuid)) {
            baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);
        }
        
        SinglePackageQueryResultDto result = new SinglePackageQueryResultDto();
        result.setPackageId(packageId);
        result.setBaselinePackage(baselinePackageGuid);
        
        //TODO
        
        return result;
    }
    
    public PaginationQueryResult<Map<String,Object>> queryDeployPackages(String unitDesignId, PaginationQuery queryObject) {
        queryObject.addEqualsFilter("unit_design", unitDesignId);
        PaginationQueryResult<Object> result = cmdbServiceV2Stub.queryCiData(cmdbDataProperties.getCiTypeIdOfPackage(), queryObject);
        PaginationQueryResult<Map<String,Object>> refinededResult = refineQueryDeployPackagesResult(result);
        return refinededResult;
    }
    
    @SuppressWarnings("unchecked")
    private PaginationQueryResult<Map<String,Object>> refineQueryDeployPackagesResult(PaginationQueryResult<Object> result){
        PaginationQueryResult<Map<String,Object>> refinededResult = new PaginationQueryResult<Map<String,Object>>();
        refinededResult.setPageInfo(result.getPageInfo());
        
        List<Map<String,Object>> refinedContents = new ArrayList<Map<String,Object>>();
        for(Object contentObj : result.getContents()) {
            if(! (contentObj instanceof Map) ) {
                log.error("Bad data type,expected:{},but:{}", Map.class.getSimpleName(), contentObj.getClass().getSimpleName());
                throw new PluginException("Bad data type.").withErrorCode("3009", Map.class.getSimpleName(), contentObj.getClass().getSimpleName());
            }
            
            Map<String,Object> contentMap = (Map<String,Object>)contentObj;
            Map<String,Object> refinedMap = refineQueryDeployPackagesResultContentMap(contentMap);
            
            refinedContents.add(refinedMap);
        }
        
        refinededResult.setContents(refinedContents);
        
        return refinededResult;
    }
    
    @SuppressWarnings("unchecked")
    private Map<String, Object> refineQueryDeployPackagesResultContentMap(Map<String,Object> contentMap){
        Map<String,Object> refinedMap = new HashMap<String, Object>();
        for(Entry<String,Object> entry : contentMap.entrySet()) {
            String key = entry.getKey();
            if("data".equals(key)) {
                Object dataObj = entry.getValue();
                Map<String,Object> dataMap = (Map<String,Object>)dataObj;
                Map<String,Object> refinedDataMap = refineQueryDeployPackagesResultDataMap(dataMap);
                
                refinedMap.put("data", refinedDataMap);
            }else {
                refinedMap.put(key, entry.getValue());
            }
        }
        
        return refinedMap;
    }
    
    private Map<String,Object> refineQueryDeployPackagesResultDataMap(Map<String,Object> dataMap){
        Map<String,Object> refinedDataMap = new HashMap<String,Object>();
        for(Entry<String,Object> dataEntry : dataMap.entrySet()) {
            String dataKey = (String)dataEntry.getKey();
            if("deploy_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String)dataEntry.getValue()));
            }else if("start_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String)dataEntry.getValue()));
            }else if("stop_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String)dataEntry.getValue()));
            }else if("diff_conf_file".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String)dataEntry.getValue()));
            }else {
                refinedDataMap.put(dataKey, dataEntry.getValue());
            }
        }
        
        return refinedDataMap;
    }
    
    private List<ConfigFileDto> parseFilePathString(String filePathString){
        List<ConfigFileDto> files = new ArrayList<ConfigFileDto>();
        if(StringUtils.isBlank(filePathString)) {
            return files;
        }
        
        log.info("filePathString:{}", filePathString);
        String [] fileStringParts = filePathString.split("\\|");
        for(String fileStringPart : fileStringParts) {
            ConfigFileDto fileDto = new ConfigFileDto();
            fileDto.setFilename(fileStringPart);
            
            files.add(fileDto);
            
            log.info("add file:{}", fileDto);
        }
        
        return files;
    }

    
    public ConfigPackageDto saveConfigFiles(String unitDesignId, String packageId, PackageDto packageDto) {
        String files = String.join("|", packageDto.getConfigFilesWithPath());
        Map<String, Object> pkg = ImmutableMap.<String, Object>builder() //
                .put("guid", packageId) //
                .put("deploy_file_path", packageDto.getDeployFile()) //
                .put("start_file_path", packageDto.getStartFile()) //
                .put("stop_file_path", packageDto.getStopFile()) //
                .put("diff_conf_file", files) //
                .put("is_decompression", packageDto.getIsDecompression()) //
                .build();
        cmdbServiceV2Stub.updateCiData(cmdbDataProperties.getCiTypeIdOfPackage(), pkg);
        
        ConfigPackageDto result = new ConfigPackageDto();
        result.setPackageId(packageId);
        result.setUnitDesignId(unitDesignId);
        
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageId(packageId);
        
        //query keys by file
        for(String filePath : packageDto.getConfigFilesWithPath()){
            log.info("try to calculate filepath:{}", filePath);
            ConfigFileDto deployConfigFile = calculatePropertyKeys(packageId, filePath, s3EndpointOfPackageId);
            result.addDeployConfigFile(deployConfigFile);
        }
        
        processDiffConfigurations(unitDesignId, packageId, result);
       
        
      
        return result;
    }
    
    private void processDiffConfigurations(String unitDesignId, String packageCiGuid, ConfigPackageDto packageConfig){
        log.info("start to process diff configurations.");
      //TODO
 //get diff guid from cmdb
        
        //create new diff if not exists
        
        Map<String,Object> packageCiDataMap = retrievePackageCiByGuid(packageCiGuid);
        
        
    }
    
    private ConfigFileDto calculatePropertyKeys(String packageId, String filePath, String s3EndpointOfPackageId) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputs = new ArrayList<>();
        inputs.add(ImmutableMap.<String, Object>builder() //
                .put("endpoint", s3EndpointOfPackageId) //
                .put("accessKey", applicationProperties.getArtifactsS3AccessKey()) //
                .put("secretKey", applicationProperties.getArtifactsS3SecretKey()) //
                .put("filePath", filePath) //
                .build()); //
        request.setInputs(inputs);
        ResultData<SaltConfigFileDto> resultData = saltstackServiceStub
                .getReleasedPackagePropertyKeysByFilePath(applicationProperties.getWecubeGatewayServerUrl(), request);
        
        ConfigFileDto configFileDto = new ConfigFileDto();
//        configFileDto.setFilePath(filePath);
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
            log.info("saltConfigKeyInfo:{}", saltConfigKeyInfo);
            ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
            configKeyInfo.setLine(saltConfigKeyInfo.getLine());
            configKeyInfo.setKey(saltConfigKeyInfo.getKey());
            configKeyInfo.setType(saltConfigKeyInfo.getType());
            
            configFileDto.addConfigKeyInfo(configKeyInfo);
        }
        
        return configFileDto;
    }
}
