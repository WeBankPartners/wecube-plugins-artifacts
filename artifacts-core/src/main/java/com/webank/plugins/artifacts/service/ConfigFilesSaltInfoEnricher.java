package com.webank.plugins.artifacts.service;

import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.webank.plugins.artifacts.dto.ConfigFileDto;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNodeDto;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNotExistException;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRemoteCallException;

public class ConfigFilesSaltInfoEnricher {
    private static final Logger log = LoggerFactory.getLogger(ConfigFilesSaltInfoEnricher.class);
    private String packageGuid;
    private Map<String, Object> packageCiMap;
    private ConfigFileManagementService service;

    public ConfigFilesSaltInfoEnricher(String packageGuid, Map<String, Object> packageCiMap,
            ConfigFileManagementService service) {
        super();
        this.packageGuid = packageGuid;
        this.packageCiMap = packageCiMap;
        this.service = service;
    }

    public List<ConfigFileDto> enrichFileInfoBySalt(List<ConfigFileDto> files) {
        if (files == null || files.isEmpty()) {
            return files;
        }

        for (ConfigFileDto f : files) {
            SaltFileNodeDto nodeDto = getSaltFileNodeBySingleFilepath(packageGuid, packageCiMap, f.getFilename());
            if (nodeDto == null) {
                log.info("Cannot find salt file node for {}", f.getFilename());
                f.setComparisonResult(AbstractArtifactService.FILE_COMP_DELETED);
                continue;
            }

            f.setMd5(nodeDto.getMd5());
            f.setIsDir(nodeDto.getIsDir());
        }

        return files;
    }

    private SaltFileNodeDto getSaltFileNodeBySingleFilepath(String packageGuid, Map<String, Object> packageCiMap,
            String filepath) {
        String s3EndpointOfPackageId = service.retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        String baseDirName = filepath.substring(0, filepath.lastIndexOf("/"));
        String filename = filepath.substring(filepath.lastIndexOf("/") + 1);
        try {
            List<SaltFileNodeDto> saltFileNodes = service.listFilesOfCurrentDirs(baseDirName, s3EndpointOfPackageId);
            for (SaltFileNodeDto dto : saltFileNodes) {
                if (filename.equals(dto.getName())) {
                    return dto;
                }
            }
        } catch (SaltFileNotExistException | SaltstackRemoteCallException e) {
            log.info("errors while list files from salt:"+e.getMessage());
        }

        return null;
    }

}
