package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.google.common.collect.ImmutableMap;
import com.webank.plugins.artifacts.dto.ConfigKeyInfoDto;
import com.webank.plugins.artifacts.dto.DeployConfigFileDto;
import com.webank.plugins.artifacts.dto.DeployPackageConfigDto;
import com.webank.plugins.artifacts.dto.PackageDto;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigFileDto;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigKeyInfoDto;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;

@Service
public class ConfigFileManagementService extends AbstractArtifactService{
    private static final Logger log = LoggerFactory.getLogger(ConfigFileManagementService.class);

    
    public DeployPackageConfigDto saveConfigFiles(String unitDesignId, String packageId, PackageDto packageDto) {
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
        
        DeployPackageConfigDto result = new DeployPackageConfigDto();
        result.setPackageId(packageId);
        result.setUnitDesignId(unitDesignId);
        
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageId(packageId);
        
        //query keys by file
        for(String filePath : packageDto.getConfigFilesWithPath()){
            log.info("try to calculate filepath:{}", filePath);
            DeployConfigFileDto deployConfigFile = calculatePropertyKeys(packageId, filePath, s3EndpointOfPackageId);
            result.addDeployConfigFile(deployConfigFile);
        }
        
        processDiffConfigurations(unitDesignId, packageId, result);
       
        
      
        return result;
    }
    
    private void processDiffConfigurations(String unitDesignId, String packageCiGuid, DeployPackageConfigDto packageConfig){
        log.info("start to process diff configurations.");
      //TODO
 //get diff guid from cmdb
        
        //create new diff if not exists
        
        Map packageCiDataMap = retrievePackageCiByGuid(packageCiGuid);
        
        
    }
    
    private DeployConfigFileDto calculatePropertyKeys(String packageId, String filePath, String s3EndpointOfPackageId) {
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
