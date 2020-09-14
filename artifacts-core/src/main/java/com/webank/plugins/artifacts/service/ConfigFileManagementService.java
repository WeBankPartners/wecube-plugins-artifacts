package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.dto.ConfigFileDto;
import com.webank.plugins.artifacts.dto.ConfigKeyInfoDto;
import com.webank.plugins.artifacts.dto.DiffConfVariableInfoDto;
import com.webank.plugins.artifacts.dto.DiffConfigurationUpdateDto;
import com.webank.plugins.artifacts.dto.FileQueryRequestDto;
import com.webank.plugins.artifacts.dto.FileQueryResultItemDto;
import com.webank.plugins.artifacts.dto.PackageComparisionRequestDto;
import com.webank.plugins.artifacts.dto.PackageComparisionResultDto;
import com.webank.plugins.artifacts.dto.PackageConfigFilesUpdateRequestDto;
import com.webank.plugins.artifacts.dto.SinglePackageQueryResultDto;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbDiffConfigDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigFileDto;
import com.webank.plugins.artifacts.support.saltstack.SaltConfigKeyInfoDto;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNodeDto;
import com.webank.plugins.artifacts.support.saltstack.SaltFileNotExistException;
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;

@Service
public class ConfigFileManagementService extends AbstractArtifactService {
    private static final Logger log = LoggerFactory.getLogger(ConfigFileManagementService.class);

    public void updateDiffConfigurations(List<DiffConfigurationUpdateDto> diffConfsToUpdate) {
        if (diffConfsToUpdate == null || diffConfsToUpdate.isEmpty()) {
            return;
        }
        List<Map<String, Object>> requestParamsMaps = new ArrayList<Map<String, Object>>();
        for (DiffConfigurationUpdateDto dto : diffConfsToUpdate) {
            Map<String, Object> requstParamsMap = new HashMap<String, Object>();
            requstParamsMap.put("id", dto.getId());
            requstParamsMap.put("variable_value", dto.getDiffExpr());

            requestParamsMaps.add(requstParamsMap);
        }

        standardCmdbEntityRestClient.updateDiffConfigurationCi(requestParamsMaps);

    }

    public SinglePackageQueryResultDto updateConfigFilesOfPackage(String unitDesignId, String packageCiGuid,
            PackageConfigFilesUpdateRequestDto packageReqDto) {

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageCiGuid);
        List<String> oldDiffConfFiles = getDiffConfFilesAsStringList(packageCiMap);
        List<ConfigFileDto> newDiffConfFiles = packageReqDto.getDiffConfFile();

        List<CmdbDiffConfigDto> allCmdbDiffConfigs = getAllCmdbDiffConfigs();
        
        List<DiffConfVariableInfoDto> diffConfVariables = packageReqDto.getDiffConfVariable();

        if (oldDiffConfFiles.isEmpty()) {
            processDiffConfFilesIfNotExistDiffConfFiles(packageCiGuid, packageCiMap, newDiffConfFiles,
                    allCmdbDiffConfigs);
        } else {
            processDiffConfFilesIfExistDiffConfFiles(packageCiGuid, packageCiMap, newDiffConfFiles, oldDiffConfFiles,
                    allCmdbDiffConfigs, diffConfVariables);
        }

        updateConfigFilesToPackageCi(packageCiGuid, packageReqDto);
        
        SinglePackageQueryResultDto packageQueryResult = querySinglePackage( unitDesignId,  packageCiGuid);

        
        return packageQueryResult;
    }

    public PackageComparisionResultDto packageComparision(String unitDesignId, String packageGuid,
            PackageComparisionRequestDto comparisonReqDto) {
        String baselinePackageGuid = comparisonReqDto.getBaselinePackageId();
        if (StringUtils.isBlank(baselinePackageGuid)) {
            throw new PluginException("Baseline package should provide.");
        }

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageGuid);
        Map<String, Object> baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);

        PackageComparisionResultDto result = buildPackageComparisionResult(packageGuid, packageCiMap);
        PackageComparisionResultDto baselineResult = buildPackageComparisionResult(baselinePackageGuid,
                baselinePackageCiMap);

        performPackageConfigComparison(result, baselineResult);

        return result;
    }

    public List<FileQueryResultItemDto> queryDeployConfigFiles(String packageCiGuid,
            FileQueryRequestDto fileQueryRequestDto) {
        List<String> inputFilePathList = fileQueryRequestDto.getFileList();
        String baselinePackageGuid = fileQueryRequestDto.getBaselinePackage();
        if (inputFilePathList == null) {
            throw new PluginException("File list cannot be null to query files.");
        }

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageCiGuid);
        Map<String, Object> baselinePackageCiMap = null;
        if (StringUtils.isNoneBlank(baselinePackageGuid)) {
            baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);
        }
        log.info("packageCiMap:{}", packageCiMap);
        List<String> filePathList = new ArrayList<String>();
        //
        if (inputFilePathList.isEmpty()) {
            // means root directory
            String rootDirName = getDeployPackageRootDir(packageCiMap);
            filePathList.add(rootDirName);
        } else {
            filePathList.addAll(inputFilePathList);
        }

        String rootDirName = getDeployPackageRootDir(packageCiMap);
        List<FileQueryResultItemDto> fileQueryResultItems = doQueryDeployConfigFiles(packageCiGuid, filePathList,
                packageCiMap, rootDirName);

        if (baselinePackageCiMap != null) {
            String baselineRootDirName = getDeployPackageRootDir(baselinePackageCiMap);
            List<FileQueryResultItemDto> baselinePackageFileQueryResultItems = doQueryDeployConfigFiles(
                    baselinePackageGuid, filePathList, baselinePackageCiMap, baselineRootDirName);
            doExecuteFileQueryComparison(fileQueryResultItems, baselinePackageFileQueryResultItems);
        }

        return fileQueryResultItems;
    }

    @SuppressWarnings("unchecked")
    public SinglePackageQueryResultDto querySinglePackage(String unitDesignId, String packageId) {
        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageId);
        log.info("currPackageCi:{}", packageCiMap);
        log.info("baseline_package:{}", packageCiMap.get("baseline_package"));
        Map<String, Object> baselinePackageCiMap = (Map<String, Object>) packageCiMap.get("baseline_package");
        String baselinePackageGuid = null;

        if (baselinePackageCiMap != null) {
            baselinePackageGuid = (String) baselinePackageCiMap.get("guid");
        }

        SinglePackageQueryResultDto result = new SinglePackageQueryResultDto();
        result.setPackageId(packageId);
        result.setBaselinePackage(baselinePackageGuid);

        Object isDecompression = packageCiMap.get("is_decompression");
        result.setIsCompress(convertCmdbObjectToBoolean(isDecompression));
        result.setStartFilePath(getStartFileInfos(packageCiMap));
        result.setDeployFilePath(getDeployFileInfos(packageCiMap));
        result.setStopFilePath(getStopFileInfos(packageCiMap));
        result.setDiffConfFile(getDiffConfFileInfos(packageCiMap));

        SinglePackageQueryResultDto baselineResult = null;
        if (StringUtils.isNoneBlank(baselinePackageGuid)) {
            baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);
            baselineResult = new SinglePackageQueryResultDto();
            baselineResult.setPackageId(baselinePackageGuid);
            baselineResult.setBaselinePackage(null);
            
            Object isDecompressionBaseline = baselinePackageCiMap.get("is_decompression");
            baselineResult.setIsCompress(convertCmdbObjectToBoolean(isDecompressionBaseline));

            baselineResult.setStartFilePath(getStartFileInfos(baselinePackageCiMap));
            baselineResult.setDeployFilePath(getDeployFileInfos(baselinePackageCiMap));
            baselineResult.setStopFilePath(getStopFileInfos(baselinePackageCiMap));
            baselineResult.setDiffConfFile(getDiffConfFileInfos(baselinePackageCiMap));
        }

        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        List<CmdbDiffConfigDto> allCmdbDiffConfigs = getAllCmdbDiffConfigs();

        Set<String> allDiffConfigKeys = new HashSet<String>();
        // process all diff files
        for (ConfigFileDto configFile : result.getDiffConfFile()) {
            List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageId, configFile.getFilename(),
                    s3EndpointOfPackageId);
            for (SaltConfigKeyInfoDto saltConfigInfo : saltConfigKeyInfos) {
                ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
                configKeyInfo.setKey(saltConfigInfo.getKey());
                configKeyInfo.setLine(saltConfigInfo.getLine());
                configKeyInfo.setType(saltConfigInfo.getType());

                configFile.addConfigKeyInfo(configKeyInfo);

                allDiffConfigKeys.add(saltConfigInfo.getKey());
            }
        }

        List<Object> boundDiffConfVariables = (List<Object>) packageCiMap.get("diff_conf_variable");

        List<DiffConfVariableInfoDto> diffConfVariables = new ArrayList<DiffConfVariableInfoDto>();
        for (String diffConfigKey : allDiffConfigKeys) {
            CmdbDiffConfigDto cmdbDiffConfig = findoutFromCmdbDiffConfigsByKey(diffConfigKey, allCmdbDiffConfigs);
            if (cmdbDiffConfig == null) {
                log.info("Cannot find cmdb diff config key:{}", diffConfigKey);
                continue;
            }
            Boolean bound = verifyIfBoundToCurrentPackage(cmdbDiffConfig, boundDiffConfVariables);

            DiffConfVariableInfoDto diffVarInfo = new DiffConfVariableInfoDto();

            diffVarInfo.setBound(bound);
            diffVarInfo.setDiffConfigGuid(cmdbDiffConfig.getGuid());
            diffVarInfo.setDiffExpr(cmdbDiffConfig.getDiffExpr());
            diffVarInfo.setKey(cmdbDiffConfig.getKey());
            diffVarInfo.setFixedDate(cmdbDiffConfig.getFixedDate());

            diffConfVariables.add(diffVarInfo);
        }

        result.setDiffConfVariable(diffConfVariables);

        return result;
    }
    
    private Boolean convertCmdbObjectToBoolean(Object obj) {
        if(obj == null) {
            return null;
        }
        
        if(obj instanceof Boolean) {
            return (Boolean)obj;
        }
        
        if(obj instanceof String) {
            if("true".equalsIgnoreCase((String)obj)){
                return true;
            }else {
                return false;
            }
        }
        
        return null;
    }

    @SuppressWarnings("unchecked")
    private Set<String> getBoundDiffConfVarGuidsFromPackage(Map<String, Object> packageCiMap) {
        Set<String> guids = new HashSet<String>();

        List<Object> boundDiffConfVariables = (List<Object>) packageCiMap.get("diff_conf_variable");
        if (boundDiffConfVariables == null || boundDiffConfVariables.isEmpty()) {
            return guids;
        }

        for (Object obj : boundDiffConfVariables) {
            if (obj == null) {
                continue;
            }
            
            if(obj instanceof Map) {
                Map<String, Object> boundDiffMap = (Map<String, Object>)obj;
                guids.add((String)boundDiffMap.get("guid"));
            }

            if (obj instanceof String) {
                guids.add((String) obj);
            }
        }

        return guids;
    }

    @SuppressWarnings("unchecked")
    private boolean verifyIfBoundToCurrentPackage(CmdbDiffConfigDto cmdbDiffConfig,
            List<Object> boundDiffConfVariables) {
        if (boundDiffConfVariables == null || boundDiffConfVariables.isEmpty()) {
            return false;
        }
        for (Object boundDiffConfVariable : boundDiffConfVariables) {
            String diffConfVarGuid = null;
            if(boundDiffConfVariable instanceof Map) {
                Map<String,Object> boundDiffConfVariableMap = (Map<String,Object>)boundDiffConfVariable;
                diffConfVarGuid = (String) boundDiffConfVariableMap.get("guid");
            }else {
                diffConfVarGuid = (String) boundDiffConfVariable;
            }
            if (diffConfVarGuid.equals(cmdbDiffConfig.getGuid())) {
                return true;
            }
        }
        return false;
    }

    private CmdbDiffConfigDto findoutFromCmdbDiffConfigsByKey(String key, List<CmdbDiffConfigDto> allCmdbDiffConfigs) {
        if (allCmdbDiffConfigs == null || allCmdbDiffConfigs.isEmpty()) {
            return null;
        }

        for (CmdbDiffConfigDto dto : allCmdbDiffConfigs) {
            if (key.equalsIgnoreCase(dto.getKey())) {
                return dto;
            }
        }

        return null;
    }

    private List<CmdbDiffConfigDto> getAllCmdbDiffConfigs() {
        List<CmdbDiffConfigDto> diffConfigs = new ArrayList<CmdbDiffConfigDto>();
        List<Map<String, Object>> diffConfigMaps = standardCmdbEntityRestClient.queryDiffConfigurations();
        for (Map<String, Object> diffConfigMap : diffConfigMaps) {
            CmdbDiffConfigDto dto = new CmdbDiffConfigDto();
            dto.setDiffExpr((String) diffConfigMap.get("variable_value"));
            dto.setGuid((String) diffConfigMap.get("guid"));
            dto.setKey((String) diffConfigMap.get("code"));
            dto.setDisplayName((String) diffConfigMap.get("displayName"));
            dto.setFixedDate((String)diffConfigMap.get("fixed_date"));

            diffConfigs.add(dto);
        }

        return diffConfigs;
    }

    private List<ConfigFileDto> getStartFileInfos(Map<String, Object> packageCiMap) {
        String filePathsStr = (String) packageCiMap.get("start_file_path");
        List<ConfigFileDto> files = parseFilePathString(filePathsStr);
        return files;
    }

    private List<ConfigFileDto> getStopFileInfos(Map<String, Object> packageCiMap) {
        String filePathsStr = (String) packageCiMap.get("stop_file_path");
        List<ConfigFileDto> files = parseFilePathString(filePathsStr);
        return files;
    }

    private List<ConfigFileDto> getDeployFileInfos(Map<String, Object> packageCiMap) {
        String filePathsStr = (String) packageCiMap.get("deploy_file_path");
        List<ConfigFileDto> files = parseFilePathString(filePathsStr);
        return files;
    }

    private List<ConfigFileDto> getDiffConfFileInfos(Map<String, Object> packageCiMap) {
        String filePathsStr = (String) packageCiMap.get("diff_conf_file");
        List<ConfigFileDto> files = parseFilePathString(filePathsStr);

        return files;
    }

    public PaginationQueryResult<Map<String, Object>> queryDeployPackages(String unitDesignId,
            PaginationQuery queryObject) {
        queryObject.addEqualsFilter("unit_design", unitDesignId);
        PaginationQueryResult<Object> result = cmdbServiceV2Stub.queryCiData(cmdbDataProperties.getCiTypeIdOfPackage(),
                queryObject);
        PaginationQueryResult<Map<String, Object>> refinededResult = refineQueryDeployPackagesResult(result);
        return refinededResult;
    }

    @SuppressWarnings("unchecked")
    private PaginationQueryResult<Map<String, Object>> refineQueryDeployPackagesResult(
            PaginationQueryResult<Object> result) {
        PaginationQueryResult<Map<String, Object>> refinededResult = new PaginationQueryResult<Map<String, Object>>();
        refinededResult.setPageInfo(result.getPageInfo());

        List<Map<String, Object>> refinedContents = new ArrayList<Map<String, Object>>();
        for (Object contentObj : result.getContents()) {
            if (!(contentObj instanceof Map)) {
                log.error("Bad data type,expected:{},but:{}", Map.class.getSimpleName(),
                        contentObj.getClass().getSimpleName());
                throw new PluginException("Bad data type.").withErrorCode("3009", Map.class.getSimpleName(),
                        contentObj.getClass().getSimpleName());
            }

            Map<String, Object> contentMap = (Map<String, Object>) contentObj;
            Map<String, Object> refinedMap = refineQueryDeployPackagesResultContentMap(contentMap);

            refinedContents.add(refinedMap);
        }

        refinededResult.setContents(refinedContents);

        return refinededResult;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> refineQueryDeployPackagesResultContentMap(Map<String, Object> contentMap) {
        Map<String, Object> refinedMap = new HashMap<String, Object>();
        for (Entry<String, Object> entry : contentMap.entrySet()) {
            String key = entry.getKey();
            if ("data".equals(key)) {
                Object dataObj = entry.getValue();
                Map<String, Object> dataMap = (Map<String, Object>) dataObj;
                Map<String, Object> refinedDataMap = refineQueryDeployPackagesResultDataMap(dataMap);

                refinedMap.put("data", refinedDataMap);
            } else {
                refinedMap.put(key, entry.getValue());
            }
        }

        return refinedMap;
    }

    private Map<String, Object> refineQueryDeployPackagesResultDataMap(Map<String, Object> dataMap) {
        Map<String, Object> refinedDataMap = new HashMap<String, Object>();
        for (Entry<String, Object> dataEntry : dataMap.entrySet()) {
            String dataKey = (String) dataEntry.getKey();
            if ("deploy_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String) dataEntry.getValue()));
            } else if ("start_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String) dataEntry.getValue()));
            } else if ("stop_file_path".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String) dataEntry.getValue()));
            } else if ("diff_conf_file".equals(dataKey)) {
                refinedDataMap.put(dataKey, parseFilePathString((String) dataEntry.getValue()));
            } else {
                refinedDataMap.put(dataKey, dataEntry.getValue());
            }
        }

        return refinedDataMap;
    }

    private List<ConfigFileDto> parseFilePathString(String filePathString) {
        List<ConfigFileDto> files = new ArrayList<ConfigFileDto>();
        if (StringUtils.isBlank(filePathString)) {
            return files;
        }

        String[] fileStringParts = filePathString.split("\\|");
        for (String fileStringPart : fileStringParts) {
            ConfigFileDto fileDto = new ConfigFileDto();
            fileDto.setFilename(fileStringPart);

            files.add(fileDto);

        }

        return files;
    }

    private String getExepectedFileName(List<ConfigFileDto> dtos) {
        if (dtos == null || dtos.isEmpty()) {
            return null;
        }

        return dtos.get(0).getFilename();
    }

    private List<SaltConfigKeyInfoDto> calculatePropertyKeys(String packageId, String filePath,
            String s3EndpointOfPackageId) {
        DefaultSaltstackRequest request = new DefaultSaltstackRequest();
        List<Map<String, Object>> inputParamMaps = new ArrayList<>();
        Map<String, Object> inputParamMap = new HashMap<String, Object>();
        inputParamMap.put("endpoint", s3EndpointOfPackageId);
        inputParamMap.put("accessKey", applicationProperties.getArtifactsS3AccessKey());
        inputParamMap.put("secretKey", applicationProperties.getArtifactsS3SecretKey());
        inputParamMap.put("filePath", filePath);

        inputParamMaps.add(inputParamMap);
        request.setInputs(inputParamMaps);
        ResultData<SaltConfigFileDto> resultData = saltstackServiceStub
                .getReleasedPackagePropertyKeysByFilePath(applicationProperties.getWecubeGatewayServerUrl(), request);

        List<SaltConfigFileDto> saltConfigFileDtos = resultData.getOutputs();
        if (saltConfigFileDtos == null || saltConfigFileDtos.isEmpty()) {
            return Collections.emptyList();
        }

        SaltConfigFileDto saltConfigFileDto = saltConfigFileDtos.get(0);

        List<SaltConfigKeyInfoDto> saltConfigKeyInfos = saltConfigFileDto.getConfigKeyInfos();
        if (saltConfigKeyInfos == null || saltConfigKeyInfos.isEmpty()) {
            return Collections.emptyList();
        }

        return saltConfigKeyInfos;
    }

    private void performPackageConfigComparison(PackageComparisionResultDto newResult,
            PackageComparisionResultDto oldResult) {
        List<ConfigFileDto> newStartFiles = newResult.getStartFilePath();
        List<ConfigFileDto> newStopFiles = newResult.getStopFilePath();
        List<ConfigFileDto> newDeployFiles = newResult.getDeployFilePath();
        List<ConfigFileDto> newDiffConfFiles = newResult.getDiffConfFile();

        List<ConfigFileDto> oldStartFiles = newConfigFileDtoList(oldResult.getStartFilePath());
        List<ConfigFileDto> oldStopFiles = newConfigFileDtoList(oldResult.getStopFilePath());
        List<ConfigFileDto> oldDeployFiles = newConfigFileDtoList(oldResult.getDeployFilePath());
        List<ConfigFileDto> oldDiffConfFiles = newConfigFileDtoList(oldResult.getDiffConfFile());

        performFileComparison(newStartFiles, oldStartFiles);

        if (!oldStartFiles.isEmpty()) {
            for (ConfigFileDto f : oldStartFiles) {
                f.setComparisonResult(FILE_COMP_DELETED);
                newResult.getStartFilePath().add(f);
            }
        }

        performFileComparison(newStopFiles, oldStopFiles);
        if (!oldStopFiles.isEmpty()) {
            for (ConfigFileDto f : oldStopFiles) {
                f.setComparisonResult(FILE_COMP_DELETED);
                newResult.getStopFilePath().add(f);
            }
        }

        performFileComparison(newDeployFiles, oldDeployFiles);
        if (!oldDeployFiles.isEmpty()) {
            for (ConfigFileDto f : oldDeployFiles) {
                f.setComparisonResult(FILE_COMP_DELETED);
                newResult.getDeployFilePath().add(f);
            }
        }

        performFileComparison(newDiffConfFiles, oldDiffConfFiles);
        if (!oldDiffConfFiles.isEmpty()) {
            for (ConfigFileDto f : oldDiffConfFiles) {
                f.setComparisonResult(FILE_COMP_DELETED);
                newResult.getDiffConfFile().add(f);
            }
        }

    }

    private void performFileComparison(List<ConfigFileDto> newFiles, List<ConfigFileDto> oldFiles) {
        for (ConfigFileDto newFile : newFiles) {
            ConfigFileDto oldFile = peekIfFoundConfigFileByFilename(newFile.getFilename(), oldFiles);
            if (oldFile == null) {
                newFile.setComparisonResult(FILE_COMP_NEW);
            } else {
                if (newFile.getMd5() != null && newFile.getMd5().equals(oldFile.getMd5())) {
                    newFile.setComparisonResult(FILE_COMP_SAME);
                } else {
                    newFile.setComparisonResult(FILE_COMP_CHANGED);
                }
            }
        }
    }

    private ConfigFileDto peekIfFoundConfigFileByFilename(String filename, List<ConfigFileDto> oldFiles) {
        if (oldFiles == null || oldFiles.isEmpty()) {
            return null;
        }
        String newFilenameWithoutPrefix = filename.substring(filename.indexOf("/"));
        ConfigFileDto foundFile = null;
        for (ConfigFileDto oldFile : oldFiles) {
            String oldFilename = oldFile.getFilename();
            String oldFilenameWithoutPrefix = oldFilename.substring(oldFilename.indexOf("/"));

            if (newFilenameWithoutPrefix.equals(oldFilenameWithoutPrefix)) {
                foundFile = oldFile;
                break;
            }
        }

        if (foundFile != null) {
            oldFiles.remove(foundFile);
        }

        return foundFile;
    }

    private List<ConfigFileDto> newConfigFileDtoList(List<ConfigFileDto> files) {
        List<ConfigFileDto> newFiles = new ArrayList<>();
        newFiles.addAll(files);

        return newFiles;
    }

    protected SaltFileNodeDto getSaltFileNodeBySingleFilepath(String packageGuid, Map<String, Object> packageCiMap,
            String filepath) {
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        String baseDirName = filepath.substring(0, filepath.lastIndexOf("/"));
        String filename = filepath.substring(filepath.lastIndexOf("/") + 1);
        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs(baseDirName, s3EndpointOfPackageId);
        for (SaltFileNodeDto dto : saltFileNodes) {
            if (filename.equals(dto.getName())) {
                return dto;
            }
        }

        return null;
    }

    private PackageComparisionResultDto buildPackageComparisionResult(String packageGuid,
            Map<String, Object> packageCiMap) {
        PackageComparisionResultDto result = new PackageComparisionResultDto();
        String packageFileName = getDeployPackageRootDir(packageCiMap);
        ConfigFilesSaltInfoEnricher enricher = new ConfigFilesSaltInfoEnricher(packageFileName, packageGuid,
                packageCiMap, this);
        List<ConfigFileDto> deployFiles = enricher.enrichFileInfoBySalt(getDeployFileInfos(packageCiMap));
        result.setDeployFilePath(deployFiles);

        List<ConfigFileDto> diffConfFiles = enricher.enrichFileInfoBySalt(getDiffConfFileInfos(packageCiMap));
        result.setDiffConfFile(diffConfFiles);

        List<ConfigFileDto> startFiles = enricher.enrichFileInfoBySalt(getStartFileInfos(packageCiMap));
        result.setStartFilePath(startFiles);

        List<ConfigFileDto> stopFiles = enricher.enrichFileInfoBySalt(getStopFileInfos(packageCiMap));
        result.setStopFilePath(stopFiles);

        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        for (ConfigFileDto configFile : result.getDiffConfFile()) {
            List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageGuid, configFile.getFilename(),
                    s3EndpointOfPackageId);
            for (SaltConfigKeyInfoDto saltConfigInfo : saltConfigKeyInfos) {
                ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
                configKeyInfo.setKey(saltConfigInfo.getKey());
                configKeyInfo.setLine(saltConfigInfo.getLine());
                configKeyInfo.setType(saltConfigInfo.getType());

                configFile.addConfigKeyInfo(configKeyInfo);

            }
        }

        return result;
    }

    private void doExecuteFileQueryComparison(List<FileQueryResultItemDto> fileQueryResultItems,
            List<FileQueryResultItemDto> baselinePackageFileQueryResultItems) {
        if (fileQueryResultItems == null || fileQueryResultItems.isEmpty()) {
            return;
        }

        int size = fileQueryResultItems.size();

        for (int idx = 0; idx < size; idx++) {
            FileQueryResultItemDto rootItem = fileQueryResultItems.get(idx);
            FileQueryResultItemDto rootBaselineItem = baselinePackageFileQueryResultItems.get(idx);

            compareRootFileQueryResultItemDto(rootItem, rootBaselineItem);
        }

    }

    private void compareRootFileQueryResultItemDto(FileQueryResultItemDto rootItem,
            FileQueryResultItemDto rootBaselineItem) {

        Map<String, FileQueryResultItemDto> fileItems = transformFileQueryResultItemDtoToMap(rootItem);
        Map<String, FileQueryResultItemDto> baselineFileItems = transformFileQueryResultItemDtoToMap(rootBaselineItem);

        for (Entry<String, FileQueryResultItemDto> fileItemEntry : fileItems.entrySet()) {
            FileQueryResultItemDto baselineItem = baselineFileItems.get(fileItemEntry.getKey());
            FileQueryResultItemDto item = fileItemEntry.getValue();
            if (baselineItem == null) {
                item.setComparisonResult(FILE_COMP_NEW);
            } else {
                if (item.getIsDir() != null && item.getIsDir()) {
                    item.setComparisonResult(FILE_COMP_SAME);
                } else {
                    String md5 = item.getMd5();
                    String baseMd5 = baselineItem.getMd5();
                    if (md5 != null && md5.equals(baseMd5)) {
                        item.setComparisonResult(FILE_COMP_SAME);
                    } else {
                        item.setComparisonResult(FILE_COMP_CHANGED);
                    }
                }
            }
        }

        findoutDeletedFiles(rootItem, rootBaselineItem, fileItems, baselineFileItems);

    }

    private void findoutDeletedFiles(FileQueryResultItemDto rootItem, FileQueryResultItemDto rootBaselineItem,
            Map<String, FileQueryResultItemDto> fileItems, Map<String, FileQueryResultItemDto> baselineFileItems) {
        List<FileQueryResultItemDto> deletedRelativeFiles = new ArrayList<FileQueryResultItemDto>();
        for (Entry<String, FileQueryResultItemDto> entry : baselineFileItems.entrySet()) {
            FileQueryResultItemDto dto = fileItems.get(entry.getKey());
            if (dto == null) {
                deletedRelativeFiles.add(entry.getValue());
            }
        }

        for (FileQueryResultItemDto deletedRelativeFile : deletedRelativeFiles) {
            String[] relativePaths = deletedRelativeFile.getRelativePath().split("/");
            String pathKey = null;
            FileQueryResultItemDto parentItem = rootItem;
            for (String relativePath : relativePaths) {
                if (pathKey == null) {
                    pathKey = relativePath;
                } else {
                    pathKey = pathKey + "/" + relativePath;
                }

                FileQueryResultItemDto item = fileItems.get(pathKey);
                if (item == null) {
                    FileQueryResultItemDto deletedBaselineItem = new FileQueryResultItemDto();
                    deletedBaselineItem.setRootDirName(rootItem.getRootDirName());
                    deletedBaselineItem.setComparisonResult(FILE_COMP_DELETED);
                    deletedBaselineItem.setExists(deletedRelativeFile.getExists());
                    deletedBaselineItem.setIsDir(deletedRelativeFile.getIsDir());
                    deletedBaselineItem.setMd5(deletedRelativeFile.getMd5());
                    deletedBaselineItem.setName(deletedRelativeFile.getName());
                    deletedBaselineItem.setPath(deletedRelativeFile.getPath());
                    deletedBaselineItem.setRelativePath(pathKey);

                    parentItem.addFileQueryResultItem(deletedBaselineItem);
                }

                parentItem = item;
            }
        }
    }

    private Map<String, FileQueryResultItemDto> transformFileQueryResultItemDtoToMap(FileQueryResultItemDto rootItem) {
        Map<String, FileQueryResultItemDto> fileItems = new HashMap<String, FileQueryResultItemDto>();
        travelTreeItems(fileItems, rootItem);

        return fileItems;
    }

    private void travelTreeItems(Map<String, FileQueryResultItemDto> fileItems, FileQueryResultItemDto item) {
        if (item == null) {
            return;
        }

        fileItems.put(item.getRelativePath(), item);
        if (item.getChildren() == null || item.getChildren().isEmpty()) {
            return;
        }

        for (FileQueryResultItemDto childItem : item.getChildren()) {
            travelTreeItems(fileItems, childItem);
        }
    }

    private String getDeployPackageRootDir(Map<String, Object> packageCiMap) {
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs("", packageEndpoint);
        return saltFileNodes.get(0).getName();
    }

    private List<FileQueryResultItemDto> doQueryDeployConfigFiles(String packageCiGuid, List<String> filePathList,
            Map<String, Object> packageCiMap, String rootDirName) {
        List<FileQueryResultItemDto> resultItemDtos = new ArrayList<FileQueryResultItemDto>();
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        for (String filePath : filePathList) {
            log.info("handle filepath:{}", filePath);
            FileQueryResultItemDto resultItemDto = queryFilesForSingleFilepath(packageCiGuid, filePath, packageCiMap,
                    packageEndpoint, rootDirName);

            resultItemDtos.add(resultItemDto);
        }
        return resultItemDtos;
    }

    private FileQueryResultItemDto queryFilesForSingleFilepath(String packageCiGuid, String filePath,
            Map<String, Object> packageCiMap, String packageEndpoint, String rootDirName) {

        
        String rawBaseName = filePath;
        if (rawBaseName.indexOf("/") > 0) {
            rawBaseName = rawBaseName.substring(0, rawBaseName.lastIndexOf("/"));
        } else {
            rawBaseName = rootDirName;
        }

        String fullFilepath = filePath;

        if (filePath.equals(rootDirName)) {
            fullFilepath = filePath;
        } else if (!filePath.startsWith(rootDirName)) {
            if (filePath.startsWith("/")) {
                fullFilepath = rootDirName + filePath;
            } else {
                fullFilepath = rootDirName + "/" + filePath;
            }
        }
        
        log.info("to process filePath:{}, fullFilepath:{}", filePath, fullFilepath);

        String baseDirName = fullFilepath;
        String fileName = null;
        if (fullFilepath.lastIndexOf("/") > 0) {
            baseDirName = fullFilepath.substring(0, fullFilepath.lastIndexOf("/"));
            fileName = fullFilepath.substring(fullFilepath.lastIndexOf("/") + 1);
        }
        
        FileQueryResultItemDto resultItemDto = new FileQueryResultItemDto();
        resultItemDto.setName(rawBaseName);
        resultItemDto.setPath(baseDirName);
        resultItemDto.setIsDir(true);
        resultItemDto.setComparisonResult(null);
        resultItemDto.setRootDirName(rootDirName);
        resultItemDto.setRelativePath(calRelativePath(baseDirName, rootDirName));

        List<SaltFileNodeDto> saltFileNodes = new ArrayList<SaltFileNodeDto>();
        try {
            saltFileNodes = listFilesOfCurrentDirs(baseDirName, packageEndpoint);
        } catch (SaltFileNotExistException e) {
            log.info("File does not exist,filename:{}", baseDirName);
            resultItemDto.setExists(false);
            resultItemDto.setComparisonResult(FILE_COMP_DELETED);
            return resultItemDto;
        }

        boolean currentFileExist = false;
        for (SaltFileNodeDto saltFileNode : saltFileNodes) {
            log.info("saltFileNode:{}", saltFileNode);
            FileQueryResultItemDto childResultItemDto = null;
            if (fileName != null && fileName.equals(saltFileNode.getName())) {
                currentFileExist = true;

                if (saltFileNode.getIsDir()) {
                    childResultItemDto = new FileQueryResultItemDto();
                    childResultItemDto.setComparisonResult(null);
                    childResultItemDto.setIsDir(true);
                    childResultItemDto.setMd5(saltFileNode.getMd5());
                    childResultItemDto.setName(fileName);
                    childResultItemDto.setRootDirName(rootDirName);
                    String tmpPath = baseDirName + "/" + saltFileNode.getName();
                    childResultItemDto.setPath(tmpPath);
                    childResultItemDto.setRelativePath(calRelativePath(tmpPath, rootDirName));

                    List<SaltFileNodeDto> childSaltFileNodes = new ArrayList<SaltFileNodeDto>();

                    try {
                        childSaltFileNodes = listFilesOfCurrentDirs(fullFilepath, packageEndpoint);
                    } catch (SaltFileNotExistException e) {
                        log.info("Child file does not exist, filename:{}", fullFilepath);
                        childResultItemDto.setExists(false);
                        childResultItemDto.setComparisonResult(FILE_COMP_DELETED);
                    }
                    for (SaltFileNodeDto childSaltFileNode : childSaltFileNodes) {
                        FileQueryResultItemDto grandResultItemDto = convertToFileQueryResultItemDto(childSaltFileNode,
                                fullFilepath, rootDirName);
                        childResultItemDto.addFileQueryResultItem(grandResultItemDto);
                    }

                } else {
                    childResultItemDto = convertToFileQueryResultItemDto(saltFileNode, baseDirName, rootDirName);
                }
            } else {
                childResultItemDto = convertToFileQueryResultItemDto(saltFileNode, baseDirName, rootDirName);
            }
            resultItemDto.addFileQueryResultItem(childResultItemDto);
        }

        if (!currentFileExist && (fileName != null)) {
            FileQueryResultItemDto noneExistResultItem = new FileQueryResultItemDto();
            noneExistResultItem.setName(fileName);
            noneExistResultItem.setExists(false);
            noneExistResultItem.setComparisonResult(FILE_COMP_DELETED);
            noneExistResultItem.setPath(fullFilepath);
            noneExistResultItem.setRootDirName(rootDirName);
            noneExistResultItem.setRelativePath(calRelativePath(fullFilepath, rootDirName));

            resultItemDto.addFileQueryResultItem(noneExistResultItem);
        }

        return resultItemDto;
    }

    private String calRelativePath(String fullPath, String rootDirName) {
        if (StringUtils.isBlank(rootDirName)) {
            return fullPath;
        }

        if (fullPath.equals(rootDirName)) {
            return fullPath;
        }

        if (fullPath.startsWith(rootDirName)) {
            return fullPath.substring(rootDirName.length() + 1);
        }

        return fullPath;
    }

    private FileQueryResultItemDto convertToFileQueryResultItemDto(SaltFileNodeDto saltFileNodeDto, String baseDirName,
            String rootDirName) {
        FileQueryResultItemDto dto = new FileQueryResultItemDto();
        dto.setComparisonResult(null);
        dto.setIsDir(saltFileNodeDto.getIsDir());
        dto.setName(saltFileNodeDto.getName());
        dto.setMd5(saltFileNodeDto.getMd5());
        dto.setRootDirName(rootDirName);
        String tmpPath = baseDirName + "/" + saltFileNodeDto.getName();
        dto.setPath(tmpPath);
        dto.setRelativePath(calRelativePath(tmpPath, rootDirName));

        return dto;
    }
    
    private boolean checkIfSameDiffConfFiles(List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles) {
        if(newDiffConfFiles.size() != oldDiffConfFiles.size()) {
            return false;
        }
        
        for(ConfigFileDto configFile : newDiffConfFiles) {
            if(!oldDiffConfFiles.contains(configFile.getFilename())) {
                return false;
            }
        }
        
        return true;
    }
    
    private void processDiffConfFilesIfSameDiffConfFiles(String packageGuid, Map<String, Object> packageCiMap,
            List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        Set<String> toBindDiffConfVarGuids = new HashSet<String>();
        
        if(diffConfVariables == null) {
            throw new PluginException("Diff conf variables cannot be null.");
        }
        
        for(DiffConfVariableInfoDto diffConfVarInfo : diffConfVariables) {
            if( (diffConfVarInfo.getBound() != null) && (diffConfVarInfo.getBound() == true)) {
                toBindDiffConfVarGuids.add(diffConfVarInfo.getDiffConfigGuid());
            }
        }
        
        this.updateDiffConfVariablesToPackageCi(packageGuid, toBindDiffConfVarGuids);
    }
    
    private void processDiffConfFilesIfModifiedDiffConfFiles(String packageGuid, Map<String, Object> packageCiMap,
            List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        List<ConfigFileDto> sameDiffFiles = new ArrayList<ConfigFileDto>();
        List<ConfigFileDto> newDiffFiles = new ArrayList<ConfigFileDto>();

        for (ConfigFileDto configFile : newDiffConfFiles) {
            String filename = configFile.getFilename();
            if (oldDiffConfFiles.contains(filename)) {
                sameDiffFiles.add(configFile);
            } else {
                newDiffFiles.add(configFile);
            }
        }

        Set<String> boundDiffConfVarGuids = getBoundDiffConfVarGuidsFromPackage(packageCiMap);
        Set<String> toBindDiffConfVarGuids = new HashSet<String>();

        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);

        for (ConfigFileDto configFile : sameDiffFiles) {
            List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageGuid, configFile.getFilename(),
                    s3EndpointOfPackageId);
            for (SaltConfigKeyInfoDto saltConfigKeyInfo : saltConfigKeyInfos) {
                ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
                configKeyInfo.setKey(saltConfigKeyInfo.getKey());
                configKeyInfo.setLine(saltConfigKeyInfo.getLine());
                configKeyInfo.setType(saltConfigKeyInfo.getType());

                configFile.addConfigKeyInfo(configKeyInfo);

                CmdbDiffConfigDto cmdbDiffConfig = findoutFromCmdbDiffConfigsByKey(saltConfigKeyInfo.getKey(),
                        allCmdbDiffConfigs);

                if (boundDiffConfVarGuids.contains(cmdbDiffConfig.getGuid())) {
                    toBindDiffConfVarGuids.add(cmdbDiffConfig.getGuid());
                }
            }
        }

        Set<String> configFileKeys = new HashSet<String>();
        for (ConfigFileDto configFile : newDiffFiles) {
            String filepath = configFile.getFilename();
            if (configFile.getIsDir()) {
                log.info("filepath {} is directory", filepath);
                continue;
            }
            List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageGuid, configFile.getFilename(),
                    s3EndpointOfPackageId);

            for (SaltConfigKeyInfoDto saltConfigKeyInfo : saltConfigKeyInfos) {
                ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
                configKeyInfo.setKey(saltConfigKeyInfo.getKey());
                configKeyInfo.setLine(saltConfigKeyInfo.getLine());
                configKeyInfo.setType(saltConfigKeyInfo.getType());

                configFile.addConfigKeyInfo(configKeyInfo);

                configFileKeys.add(saltConfigKeyInfo.getKey());
            }
        }

        for (String configFileKey : configFileKeys) {
            CmdbDiffConfigDto cmdbDiffConfig = findoutFromCmdbDiffConfigsByKey(configFileKey, allCmdbDiffConfigs);
            if (cmdbDiffConfig == null) {
                CmdbDiffConfigDto newCmdbDiffConfig = this.standardCmdbEntityRestClient
                        .createDiffConfigurationCi(configFileKey, null);
                if (newCmdbDiffConfig == null) {
                    throw new PluginException("Failed to create new Diff configuration key:{}", configFileKey);
                }

                allCmdbDiffConfigs.add(cmdbDiffConfig);
                toBindDiffConfVarGuids.add(newCmdbDiffConfig.getGuid());
            } else {
                toBindDiffConfVarGuids.add(cmdbDiffConfig.getGuid());
            }
        }

        this.updateDiffConfVariablesToPackageCi(packageGuid, toBindDiffConfVarGuids);
    }

    private void processDiffConfFilesIfExistDiffConfFiles(String packageGuid, Map<String, Object> packageCiMap,
            List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        //TODO
        if(checkIfSameDiffConfFiles(newDiffConfFiles, oldDiffConfFiles)) {
            processDiffConfFilesIfSameDiffConfFiles( packageGuid, packageCiMap,
                     newDiffConfFiles,  oldDiffConfFiles,
                     allCmdbDiffConfigs, diffConfVariables);
            
            return;
        }else {
            processDiffConfFilesIfModifiedDiffConfFiles( packageGuid,  packageCiMap,
                     newDiffConfFiles, oldDiffConfFiles,
                     allCmdbDiffConfigs,  diffConfVariables);
        }
        
        

    }

    private void processDiffConfFilesIfNotExistDiffConfFiles(String packageGuid, Map<String, Object> packageCiMap,
            List<ConfigFileDto> newDiffConfFiles, List<CmdbDiffConfigDto> allCmdbDiffConfigs) {
        if (newDiffConfFiles == null || newDiffConfFiles.isEmpty()) {
            return;
        }
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        Set<String> configFileKeys = new HashSet<String>();
        for (ConfigFileDto configFile : newDiffConfFiles) {
            String filepath = configFile.getFilename();
            if (configFile.getIsDir()) {
                log.info("filepath {} is directory", filepath);
                continue;
            }

            List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageGuid, filepath,
                    s3EndpointOfPackageId);

            for (SaltConfigKeyInfoDto saltConfigKeyInfo : saltConfigKeyInfos) {
                ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
                configKeyInfo.setKey(saltConfigKeyInfo.getKey());
                configKeyInfo.setLine(saltConfigKeyInfo.getLine());
                configKeyInfo.setType(saltConfigKeyInfo.getType());

                configFile.addConfigKeyInfo(configKeyInfo);

                configFileKeys.add(saltConfigKeyInfo.getKey());
            }
        }

        List<String> toBoundDiffConfVariableGuids = new ArrayList<String>();
        for (String configFileKey : configFileKeys) {
            CmdbDiffConfigDto cmdbDiffConfig = findoutFromCmdbDiffConfigsByKey(configFileKey, allCmdbDiffConfigs);
            if (cmdbDiffConfig == null) {
                CmdbDiffConfigDto newCmdbDiffConfig = this.standardCmdbEntityRestClient
                        .createDiffConfigurationCi(configFileKey, null);
                if (newCmdbDiffConfig == null) {
                    throw new PluginException("Failed to create new Diff configuration key:{}", configFileKey);
                }

                allCmdbDiffConfigs.add(cmdbDiffConfig);
                toBoundDiffConfVariableGuids.add(newCmdbDiffConfig.getGuid());
            } else {
                if (!toBoundDiffConfVariableGuids.contains(cmdbDiffConfig.getGuid())) {
                    toBoundDiffConfVariableGuids.add(cmdbDiffConfig.getGuid());
                }
            }
        }

        this.updateDiffConfVariablesToPackageCi(packageGuid, toBoundDiffConfVariableGuids);

    }

    private String assembleDiffConfigFileString(List<ConfigFileDto> diffConfFiles) {
        String diffConfigFileStr = String.join("|", diffConfFiles.stream().map(dto -> {
            return dto.getFilename();
        }).collect(Collectors.toList()));

        return diffConfigFileStr;
    }

    private void updateDiffConfVariablesToPackageCi(String packageCiGuid, Collection<String> diffConfVariableGuids) {
        List<String> guids = new ArrayList<String>();
        guids.addAll(diffConfVariableGuids);
        Map<String, Object> packageUpdateParams = new HashMap<String, Object>();
        packageUpdateParams.put("guid", packageCiGuid);
        packageUpdateParams.put("diff_conf_variable", guids);
        this.updatePackageCi(packageUpdateParams);
    }

    private void updateConfigFilesToPackageCi(String packageCiGuid, PackageConfigFilesUpdateRequestDto packageReqDto) {
        List<ConfigFileDto> newDiffConfFiles = packageReqDto.getDiffConfFile();
        String diffConfigFileStr = assembleDiffConfigFileString(newDiffConfFiles);

        Map<String, Object> packageUpdateParams = new HashMap<String, Object>();
        packageUpdateParams.put("guid", packageCiGuid);
        packageUpdateParams.put("deploy_file_path", getExepectedFileName(packageReqDto.getDeployFilePath()));
        packageUpdateParams.put("start_file_path", getExepectedFileName(packageReqDto.getStartFilePath()));
        packageUpdateParams.put("stop_file_path", getExepectedFileName(packageReqDto.getStopFilePath()));
        packageUpdateParams.put("is_decompression", packageReqDto.getIsDecompression());
        packageUpdateParams.put("diff_conf_file", diffConfigFileStr);

        this.updatePackageCi(packageUpdateParams);
    }

    private List<String> getDiffConfFilesAsStringList(Map<String, Object> packageCiMap) {
        String diffConfFileStr = (String) packageCiMap.get("diff_conf_file");
        List<String> diffConfFiles = new ArrayList<String>();

        if (StringUtils.isBlank(diffConfFileStr)) {
            return diffConfFiles;
        }

        String[] diffConfFileStrParts = diffConfFileStr.split("\\|");
        for (String diffConfFileStrPart : diffConfFileStrParts) {
            diffConfFiles.add(diffConfFileStrPart);
        }

        return diffConfFiles;
    }
}
