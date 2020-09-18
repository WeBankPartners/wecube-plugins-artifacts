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
import com.webank.plugins.artifacts.support.saltstack.SaltstackRemoteCallException;
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

        SinglePackageQueryResultDto packageUpdateResult = new SinglePackageQueryResultDto();
        packageUpdateResult.setPackageId(packageCiGuid);

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageCiGuid);
//        String baselinePackageGuid = getBaselinePackageGuidFromCiMap(packageCiMap);
//        packageUpdateResult.setBaselinePackage(baselinePackageGuid);
        List<String> oldDiffConfFiles = getDiffConfFilesAsStringList(packageCiMap);
        List<ConfigFileDto> newDiffConfFiles = packageReqDto.getDiffConfFile();

        List<CmdbDiffConfigDto> allCmdbDiffConfigs = getAllCmdbDiffConfigs();

        List<DiffConfVariableInfoDto> diffConfVariables = packageReqDto.getDiffConfVariable();

        if (oldDiffConfFiles.isEmpty()) {
            processDiffConfFilesIfNotExistDiffConfFiles(packageUpdateResult, packageCiMap, newDiffConfFiles,
                    allCmdbDiffConfigs);
        } else {
            processDiffConfFilesIfExistDiffConfFiles(packageUpdateResult, packageCiMap, newDiffConfFiles,
                    oldDiffConfFiles, allCmdbDiffConfigs, diffConfVariables);
        }

        updateConfigFilesToPackageCi(packageUpdateResult, packageReqDto);

//        packageUpdateResult.setIsDecompression(packageReqDto.getIsDecompression());
        packageUpdateResult = querySinglePackage(unitDesignId, packageCiGuid);

        return packageUpdateResult;
    }

    public PackageComparisionResultDto packageComparision(String unitDesignId, String packageGuid,
            PackageComparisionRequestDto comparisonReqDto) {
        String baselinePackageGuid = comparisonReqDto.getBaselinePackage();
        if (StringUtils.isBlank(baselinePackageGuid)) {
            throw new PluginException("Baseline package should provide.");
        }

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageGuid);
        Map<String, Object> baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);

        PackageComparisionResultDto result = buildPackageComparisionResult(packageGuid, packageCiMap, baselinePackageCiMap, false);
        PackageComparisionResultDto baselineResult = buildPackageComparisionResult(baselinePackageGuid,
                baselinePackageCiMap,baselinePackageCiMap, true);

        performPackageConfigComparison(result, baselineResult);

        return result;
    }

    public List<FileQueryResultItemDto> queryDeployConfigFiles(String packageCiGuid,
            FileQueryRequestDto fileQueryRequestDto) {
        List<String> inputFilepathList = fileQueryRequestDto.getFileList();
        String baselinePackageGuid = fileQueryRequestDto.getBaselinePackage();
        if (inputFilepathList == null) {
            throw new PluginException("File list cannot be null to query files.");
        }

        boolean expendAll = fileQueryRequestDto.getExpandAll();

        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageCiGuid);

        log.info("packageCiMap:{}", packageCiMap);
        List<String> filepathList = new ArrayList<String>();
        //
        if (inputFilepathList.isEmpty()) {
//            String rootDirName = getDeployPackageRootDirName(packageCiMap);
            filepathList.add("");
        } else {
            filepathList.addAll(inputFilepathList);
        }

        List<FileQueryResultItemDto> fileQueryResultItems = doQueryDeployConfigFiles(packageCiGuid, filepathList,
                packageCiMap, expendAll);

        Map<String, Object> baselinePackageCiMap = null;
        if (StringUtils.isNoneBlank(baselinePackageGuid)) {
            baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);
        }
        if (baselinePackageCiMap != null) {
            List<FileQueryResultItemDto> baselinePackageFileQueryResultItems = doQueryDeployConfigFiles(
                    baselinePackageGuid, filepathList, baselinePackageCiMap, expendAll);
            doExecuteFileQueryComparison(fileQueryResultItems, baselinePackageFileQueryResultItems);
        }

        return fileQueryResultItems;
    }

    @SuppressWarnings("unchecked")
    public SinglePackageQueryResultDto querySinglePackage(String unitDesignId, String packageId) {
        Map<String, Object> packageCiMap = retrievePackageCiByGuid(packageId);
        log.info("currPackageCi:{}", packageCiMap);
        log.info("baseline_package:{}", packageCiMap.get("baseline_package"));
        String baselinePackageGuid = getBaselinePackageGuidFromCiMap(packageCiMap);

        SinglePackageQueryResultDto result = new SinglePackageQueryResultDto();
        result.setPackageId(packageId);
        result.setBaselinePackage(baselinePackageGuid);
        ConfigFilesSaltInfoEnricher currentEnricher = new ConfigFilesSaltInfoEnricher(packageId, packageCiMap,
            this);

        Object isDecompression = packageCiMap.get("is_decompression");
        result.setIsDecompression(convertCmdbObjectToBoolean(isDecompression));
        result.setStartFilePath(currentEnricher.enrichFileInfoBySalt(getStartFileInfos(packageCiMap)));
        result.setDeployFilePath(currentEnricher.enrichFileInfoBySalt(getDeployFileInfos(packageCiMap)));
        result.setStopFilePath(currentEnricher.enrichFileInfoBySalt(getStopFileInfos(packageCiMap)));
        result.setDiffConfFile(currentEnricher.enrichFileInfoBySalt(getDiffConfFileInfos(packageCiMap)));

        SinglePackageQueryResultDto baselineResult = null;
        if (StringUtils.isNoneBlank(baselinePackageGuid)) {
            Map<String, Object> baselinePackageCiMap = retrievePackageCiByGuid(baselinePackageGuid);
            ConfigFilesSaltInfoEnricher baselineEnricher = new ConfigFilesSaltInfoEnricher(baselinePackageGuid, baselinePackageCiMap,
                    this);
            baselineResult = new SinglePackageQueryResultDto();
            baselineResult.setPackageId(baselinePackageGuid);
            baselineResult.setBaselinePackage(null);

            Object isDecompressionBaseline = baselinePackageCiMap.get("is_decompression");
            baselineResult.setIsDecompression(convertCmdbObjectToBoolean(isDecompressionBaseline));

            baselineResult.setStartFilePath(baselineEnricher.enrichFileInfoBySalt(getStartFileInfos(baselinePackageCiMap)));
            baselineResult.setDeployFilePath(baselineEnricher.enrichFileInfoBySalt(getDeployFileInfos(baselinePackageCiMap)));
            baselineResult.setStopFilePath(baselineEnricher.enrichFileInfoBySalt(getStopFileInfos(baselinePackageCiMap)));
            baselineResult.setDiffConfFile(baselineEnricher.enrichFileInfoBySalt(getDiffConfFileInfos(baselinePackageCiMap)));

            doCompareFilesWithBaselineFiles(result, baselineResult);
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

    private void doCompareFilesWithBaselineFiles(SinglePackageQueryResultDto newResult,
            SinglePackageQueryResultDto oldResult) {
        List<ConfigFileDto> newStartFiles = newResult.getStartFilePath();
        List<ConfigFileDto> newStopFiles = newResult.getStopFilePath();
        List<ConfigFileDto> newDeployFiles = newResult.getDeployFilePath();
        List<ConfigFileDto> newDiffConfFiles = newResult.getDiffConfFile();

        List<ConfigFileDto> oldStartFiles = newConfigFileDtoList(oldResult.getStartFilePath());
        List<ConfigFileDto> oldStopFiles = newConfigFileDtoList(oldResult.getStopFilePath());
        List<ConfigFileDto> oldDeployFiles = newConfigFileDtoList(oldResult.getDeployFilePath());
        List<ConfigFileDto> oldDiffConfFiles = newConfigFileDtoList(oldResult.getDiffConfFile());

        performFileComparison(newStartFiles, oldStartFiles);

//        if (!oldStartFiles.isEmpty()) {
//            for (ConfigFileDto f : oldStartFiles) {
//                f.setComparisonResult(FILE_COMP_DELETED);
//                newResult.getStartFilePath().add(f);
//            }
//        }

        performFileComparison(newStopFiles, oldStopFiles);
//        if (!oldStopFiles.isEmpty()) {
//            for (ConfigFileDto f : oldStopFiles) {
//                f.setComparisonResult(FILE_COMP_DELETED);
//                newResult.getStopFilePath().add(f);
//            }
//        }

        performFileComparison(newDeployFiles, oldDeployFiles);
//        if (!oldDeployFiles.isEmpty()) {
//            for (ConfigFileDto f : oldDeployFiles) {
//                f.setComparisonResult(FILE_COMP_DELETED);
//                newResult.getDeployFilePath().add(f);
//            }
//        }

        performFileComparison(newDiffConfFiles, oldDiffConfFiles);
//        if (!oldDiffConfFiles.isEmpty()) {
//            for (ConfigFileDto f : oldDiffConfFiles) {
//                f.setComparisonResult(FILE_COMP_DELETED);
//                newResult.getDiffConfFile().add(f);
//            }
//        }

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
            dto.setFixedDate((String) diffConfigMap.get("fixed_date"));

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
        ResultData<SaltConfigFileDto> resultData = null;
        try {
            resultData = saltstackServiceStub.getReleasedPackagePropertyKeysByFilePath(
                    applicationProperties.getWecubeGatewayServerUrl(), request);
        } catch (SaltstackRemoteCallException e) {
            log.info("errors to get conf key from {},error:{}", filePath, e.getMessage());
            return Collections.emptyList();
        }

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
                if(FILE_COMP_DELETED.equals(newFile.getComparisonResult())) {
                    //nothing
                }else {
                    newFile.setComparisonResult(FILE_COMP_NEW);
                }
            } else {
                if(FILE_COMP_DELETED.equals(oldFile.getComparisonResult())) {
                    if(FILE_COMP_DELETED.equals(newFile.getComparisonResult())) {
                        //nothing
                    }else {
                        newFile.setComparisonResult(FILE_COMP_NEW);
                    }
                }else {
                    if(FILE_COMP_DELETED.equals(newFile.getComparisonResult())) {
                        //nothing
                    }else{
                        if (newFile.getMd5() != null && newFile.getMd5().equals(oldFile.getMd5())) {
                            newFile.setComparisonResult(FILE_COMP_SAME);
                        } else {
                            newFile.setComparisonResult(FILE_COMP_CHANGED);
                        }
                    }
                   
                }
            }
        }
    }

    private ConfigFileDto peekIfFoundConfigFileByFilename(String filename, List<ConfigFileDto> oldFiles) {
        if (oldFiles == null || oldFiles.isEmpty()) {
            return null;
        }
//        String newFilenameWithoutPrefix = filename.substring(filename.indexOf("/"));
        ConfigFileDto foundFile = null;
        for (ConfigFileDto oldFile : oldFiles) {
            String oldFilename = oldFile.getFilename();
//            String oldFilenameWithoutPrefix = oldFilename.substring(oldFilename.indexOf("/"));

            if (filename.equals(oldFilename)) {
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

    private SaltFileNodeDto getSaltFileNodeBySingleFilepath(String packageGuid, Map<String, Object> packageCiMap,
            String filepath, String rootDirName) {
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        List<SaltFileNodeDto> saltFileNodes = null;
        if (rootDirName.equals(filepath)) {
            try {
                saltFileNodes = listFilesOfCurrentDirs(filepath, s3EndpointOfPackageId);
                SaltFileNodeDto fileNode = new SaltFileNodeDto();
                fileNode.setIsDir(true);
                fileNode.setMd5(null);
                fileNode.setName(filepath);
                fileNode.setPath(filepath);
                return fileNode;
            } catch (SaltFileNotExistException e) {
                log.info("file not exist:{}", filepath);
                return null;
            }
        }
        
        if(filepath.startsWith("/") && filepath.length() > 1) {
            filepath = filepath.substring(1);
        }

        String baseDirName = "";
        String filename = filepath;
        if(filepath.indexOf("/") > 0) {
            baseDirName = filepath.substring(0, filepath.lastIndexOf("/"));
            filename = filepath.substring(filepath.lastIndexOf("/") + 1);
        }
        try {
            saltFileNodes = listFilesOfCurrentDirs(baseDirName, s3EndpointOfPackageId);
        } catch (SaltFileNotExistException e) {
            log.info("file not exist:{}", filepath);
            return null;
        }
        for (SaltFileNodeDto dto : saltFileNodes) {
            if (filename.equals(dto.getName())) {
                return dto;
            }
        }

        return null;
    }

    private PackageComparisionResultDto buildPackageComparisionResult(String packageGuid,
            Map<String, Object> packageCiMap, Map<String, Object> baselinePackageCiMap, boolean isBaseline) {
        Map<String, Object>  configFilesSrcPackageMap = null;
        if (isBaseline) {
            configFilesSrcPackageMap = packageCiMap;
        }else {
            configFilesSrcPackageMap = baselinePackageCiMap;
        }
        PackageComparisionResultDto result = new PackageComparisionResultDto();
        ConfigFilesSaltInfoEnricher enricher = new ConfigFilesSaltInfoEnricher(packageGuid, packageCiMap, this);
        List<ConfigFileDto> deployFiles = enricher.enrichFileInfoBySalt(getDeployFileInfos(configFilesSrcPackageMap));
        result.setDeployFilePath(deployFiles);

        List<ConfigFileDto> diffConfFiles = enricher.enrichFileInfoBySalt(getDiffConfFileInfos(configFilesSrcPackageMap));
        result.setDiffConfFile(diffConfFiles);

        List<ConfigFileDto> startFiles = enricher.enrichFileInfoBySalt(getStartFileInfos(configFilesSrcPackageMap));
        result.setStartFilePath(startFiles);

        List<ConfigFileDto> stopFiles = enricher.enrichFileInfoBySalt(getStopFileInfos(configFilesSrcPackageMap));
        result.setStopFilePath(stopFiles);

//        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
//        for (ConfigFileDto configFile : result.getDiffConfFile()) {
//            try {
//                List<SaltConfigKeyInfoDto> saltConfigKeyInfos = calculatePropertyKeys(packageGuid,
//                        configFile.getFilename(), s3EndpointOfPackageId);
//                for (SaltConfigKeyInfoDto saltConfigInfo : saltConfigKeyInfos) {
//                    ConfigKeyInfoDto configKeyInfo = new ConfigKeyInfoDto();
//                    configKeyInfo.setKey(saltConfigInfo.getKey());
//                    configKeyInfo.setLine(saltConfigInfo.getLine());
//                    configKeyInfo.setType(saltConfigInfo.getType());
//
//                    configFile.addConfigKeyInfo(configKeyInfo);
//
//                }
//            } catch (SaltstackRemoteCallException e) {
//                log.info("errors to get keys from {},error:{}", configFile.getFilename(), e.getMessage());
//            }
//        }

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
            FileQueryResultItemDto rootBaselineItem = findoutFileQueryResultItemByName(rootItem.getName(), baselinePackageFileQueryResultItems);

            if(rootBaselineItem != null) {
                compareRootFileQueryResultItemDto(rootItem, rootBaselineItem);
            }else {
                if(FILE_COMP_DELETED.equals(rootItem.getComparisonResult())) {
                    //nothing
                }else {
                    rootItem.setComparisonResult(FILE_COMP_NEW);
                }
            }
        }

    }
    
    private FileQueryResultItemDto findoutFileQueryResultItemByName(String name,List<FileQueryResultItemDto> baselinePackageFileQueryResultItems) {
        if(baselinePackageFileQueryResultItems == null || baselinePackageFileQueryResultItems.isEmpty()) {
            return null;
        }
        
        for(FileQueryResultItemDto item : baselinePackageFileQueryResultItems) {
            if(name.equals(item.getName())) {
                return item;
            }
        }
        
        return null;
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
                if (FILE_COMP_DELETED.equals(item.getComparisonResult())) {
                    continue;
                }

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
            String[] relativePaths = deletedRelativeFile.getPath().split("/");
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
                    item = new FileQueryResultItemDto();
                    item.setComparisonResult(FILE_COMP_DELETED);
                    item.setExists(deletedRelativeFile.getExists());
                    item.setIsDir(deletedRelativeFile.getIsDir());
                    item.setMd5(deletedRelativeFile.getMd5());
                    item.setName(deletedRelativeFile.getName());
                    item.setPath(deletedRelativeFile.getPath());

                    parentItem.addFileQueryResultItem(item);
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

        fileItems.put(item.getPath(), item);
        if (item.getChildren() == null || item.getChildren().isEmpty()) {
            return;
        }

        for (FileQueryResultItemDto childItem : item.getChildren()) {
            travelTreeItems(fileItems, childItem);
        }
    }

    private String getDeployPackageRootDirName(Map<String, Object> packageCiMap) {
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs("", packageEndpoint);
        return saltFileNodes.get(0).getName();
    }

    private List<FileQueryResultItemDto> doQueryDeployConfigFiles(String packageCiGuid, List<String> filePathList,
            Map<String, Object> packageCiMap, boolean expendAll) {
        List<FileQueryResultItemDto> fileQueryResultItems = new ArrayList<FileQueryResultItemDto>();
        Map<String, FileQueryResultItemDto> pathAndFileQueryResultItems = new HashMap<String, FileQueryResultItemDto>();
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        for (String filepath : filePathList) {
            log.info("handle filepath:{}", filepath);
            queryFilesForSingleFilepath(packageCiGuid, filepath, packageCiMap, packageEndpoint, fileQueryResultItems,
                    pathAndFileQueryResultItems, expendAll);

        }
        return fileQueryResultItems;
    }

    private FileQueryResultItemDto buildFileQueryResultItemDto(SaltFileNodeDto saltFileNode) {
        FileQueryResultItemDto fileQueryResultItem = new FileQueryResultItemDto();
        fileQueryResultItem.setIsDir(saltFileNode.getIsDir());
        fileQueryResultItem.setExists(true);
        fileQueryResultItem.setMd5(fileQueryResultItem.getMd5());
        fileQueryResultItem.setName(saltFileNode.getName());

        return fileQueryResultItem;
    }

    private void queryFilesForRootDir(String packageEndpoint, List<FileQueryResultItemDto> fileQueryResultItems,
            Map<String, FileQueryResultItemDto> pathAndFileQueryResultItems) {
        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs("", packageEndpoint);
        if (saltFileNodes == null) {
            return;
        }

        for (SaltFileNodeDto saltFileNode : saltFileNodes) {
            FileQueryResultItemDto fileQueryResultItem = pathAndFileQueryResultItems.get(saltFileNode.getName());
            if (fileQueryResultItem == null) {
                fileQueryResultItem = buildFileQueryResultItemDto(saltFileNode);
                fileQueryResultItem.setPath(saltFileNode.getName());

                fileQueryResultItems.add(fileQueryResultItem);
                pathAndFileQueryResultItems.put(fileQueryResultItem.getPath(), fileQueryResultItem);
            }
        }
    }

    private void queryFilesForSingleFilepathExpendAll(String packageCiGuid, String filepath,
            Map<String, Object> packageCiMap, String packageEndpoint, List<FileQueryResultItemDto> fileQueryResultItems,
            Map<String, FileQueryResultItemDto> pathAndFileQueryResultItems) {
        queryFilesForRootDir(packageEndpoint, fileQueryResultItems, pathAndFileQueryResultItems);
        String[] filepathParts = filepath.split("/");

        String rootFilepath = filepathParts[0];
        FileQueryResultItemDto rootResultItem = pathAndFileQueryResultItems.get(rootFilepath);
        if (rootResultItem == null) {
            rootResultItem = new FileQueryResultItemDto();
            rootResultItem.setIsDir(true);
            rootResultItem.setName(rootFilepath);
            rootResultItem.setPath(rootFilepath);

            fileQueryResultItems.add(rootResultItem);
            pathAndFileQueryResultItems.put(rootResultItem.getPath(), rootResultItem);
        }

        List<SaltFileNodeDto> saltFileNodes = new ArrayList<SaltFileNodeDto>();
        try {
            saltFileNodes = listFilesOfCurrentDirs(rootFilepath, packageEndpoint);
            for (SaltFileNodeDto saltFileNode : saltFileNodes) {
                String childFilePath = rootFilepath + "/" + saltFileNode.getName();
                FileQueryResultItemDto childRootResultItem = pathAndFileQueryResultItems.get(childFilePath);
                if (childRootResultItem == null) {
                    childRootResultItem = new FileQueryResultItemDto();
                    childRootResultItem.setExists(true);
                    childRootResultItem.setIsDir(saltFileNode.getIsDir());
                    childRootResultItem.setMd5(saltFileNode.getMd5());
                    childRootResultItem.setName(saltFileNode.getName());
                    childRootResultItem.setPath(childFilePath);

                    rootResultItem.addFileQueryResultItem(childRootResultItem);
                    pathAndFileQueryResultItems.put(childRootResultItem.getPath(), childRootResultItem);
                }
            }
        } catch (SaltFileNotExistException e) {
            log.info("File does not exist,filename:{}", rootResultItem);
            rootResultItem.setExists(false);
            rootResultItem.setComparisonResult(FILE_COMP_DELETED);
            if(filepathParts.length == 1) {
                rootResultItem.setIsDir(false);
            }
        }

        String parentPath = rootFilepath;
        FileQueryResultItemDto parentFileQueryResultItem = rootResultItem;
        for (int index = 1; index < filepathParts.length; index++) {
            String filepathPart = filepathParts[index];

            String fullFilepath = parentPath + "/" + filepathPart;
            FileQueryResultItemDto currentResultItem = pathAndFileQueryResultItems.get(fullFilepath);
            if (currentResultItem == null) {
                currentResultItem = new FileQueryResultItemDto();
                currentResultItem.setPath(fullFilepath);
                currentResultItem.setName(filepathPart);
                currentResultItem.setComparisonResult(FILE_COMP_DELETED);
                currentResultItem.setExists(false);
                if(index == (filepathParts.length -1)) {
                    currentResultItem.setIsDir(false);
                }else {
                    currentResultItem.setIsDir(true);
                }

                parentFileQueryResultItem.addFileQueryResultItem(currentResultItem);
                pathAndFileQueryResultItems.put(currentResultItem.getPath(), currentResultItem);
            } else {
                if (currentResultItem.getExists() && currentResultItem.getIsDir()) {
                    List<SaltFileNodeDto> childSaltFileNodes = new ArrayList<SaltFileNodeDto>();
                    try {
                        childSaltFileNodes = listFilesOfCurrentDirs(fullFilepath, packageEndpoint);
                        for (SaltFileNodeDto saltFileNode : childSaltFileNodes) {
                            String childFilePath = fullFilepath + "/" + saltFileNode.getName();
                            FileQueryResultItemDto childRootResultItem = pathAndFileQueryResultItems.get(childFilePath);
                            if (childRootResultItem == null) {
                                childRootResultItem = new FileQueryResultItemDto();
                                childRootResultItem.setExists(true);
                                childRootResultItem.setIsDir(saltFileNode.getIsDir());
                                childRootResultItem.setMd5(saltFileNode.getMd5());
                                childRootResultItem.setName(saltFileNode.getName());
                                childRootResultItem.setPath(childFilePath);

                                currentResultItem.addFileQueryResultItem(childRootResultItem);
                                pathAndFileQueryResultItems.put(childRootResultItem.getPath(), childRootResultItem);
                            }
                        }
                    } catch (SaltFileNotExistException e) {
                        log.info("File does not exist,filename:{}", rootResultItem);
                        currentResultItem.setExists(false);
                        currentResultItem.setComparisonResult(FILE_COMP_DELETED);
                    }
                }
            }

            parentFileQueryResultItem = currentResultItem;
            parentPath = fullFilepath;

        }
    }

    private void queryFilesForSingleFilepathNotExpendAll(String packageCiGuid, String filepath,
            Map<String, Object> packageCiMap, String packageEndpoint, List<FileQueryResultItemDto> fileQueryResultItems,
            Map<String, FileQueryResultItemDto> pathAndFileQueryResultItems) {

        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs(filepath, packageEndpoint);
        for (SaltFileNodeDto saltFileNode : saltFileNodes) {
            String childFilePath = filepath + "/" + saltFileNode.getName();
            FileQueryResultItemDto childRootResultItem = pathAndFileQueryResultItems.get(childFilePath);
            if (childRootResultItem == null) {
                childRootResultItem = new FileQueryResultItemDto();
                childRootResultItem.setExists(true);
                childRootResultItem.setIsDir(saltFileNode.getIsDir());
                childRootResultItem.setMd5(saltFileNode.getMd5());
                childRootResultItem.setName(saltFileNode.getName());
                childRootResultItem.setPath(childFilePath);

                fileQueryResultItems.add(childRootResultItem);
                pathAndFileQueryResultItems.put(childRootResultItem.getPath(), childRootResultItem);
            }
        }

    }

    private void queryFilesForSingleFilepath(String packageCiGuid, String filepath, Map<String, Object> packageCiMap,
            String packageEndpoint, List<FileQueryResultItemDto> fileQueryResultItems,
            Map<String, FileQueryResultItemDto> pathAndFileQueryResultItems, boolean expendAll) {

        if ("".equals(filepath)) {
            queryFilesForRootDir(packageEndpoint, fileQueryResultItems, pathAndFileQueryResultItems);
            return;
        }

        if (expendAll) {
            queryFilesForSingleFilepathExpendAll(packageCiGuid, filepath, packageCiMap, packageEndpoint,
                    fileQueryResultItems, pathAndFileQueryResultItems);

            return;
        } else {
            queryFilesForSingleFilepathNotExpendAll(packageCiGuid, filepath, packageCiMap, packageEndpoint,
                    fileQueryResultItems, pathAndFileQueryResultItems);

            return;
        }
    }

    private boolean checkIfSameDiffConfFiles(List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles) {
        if (newDiffConfFiles.size() != oldDiffConfFiles.size()) {
            return false;
        }

        for (ConfigFileDto configFile : newDiffConfFiles) {
            if (!oldDiffConfFiles.contains(configFile.getFilename())) {
                return false;
            }
        }

        return true;
    }

    private void processDiffConfFilesIfSameDiffConfFiles(SinglePackageQueryResultDto packageUpdateResult,
            Map<String, Object> packageCiMap, List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        Set<String> toBindDiffConfVarGuids = new HashSet<String>();

        if (diffConfVariables == null) {
            throw new PluginException("Diff conf variables cannot be null.");
        }

        for (DiffConfVariableInfoDto diffConfVarInfo : diffConfVariables) {
            if ((diffConfVarInfo.getBound() != null) && (diffConfVarInfo.getBound() == true)) {
                toBindDiffConfVarGuids.add(diffConfVarInfo.getDiffConfigGuid());
            }
        }

        this.updateDiffConfVariablesToPackageCi(packageUpdateResult.getPackageId(), toBindDiffConfVarGuids);
    }

    private void processDiffConfFilesIfModifiedDiffConfFiles(SinglePackageQueryResultDto packageUpdateResult,
            Map<String, Object> packageCiMap, List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        String packageGuid = packageUpdateResult.getPackageId();
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

        String rootDirName = getDeployPackageRootDirName(packageCiMap);

        Set<String> configFileKeys = new HashSet<String>();
        for (ConfigFileDto configFile : newDiffFiles) {
            SaltFileNodeDto saltFileNode = getSaltFileNodeBySingleFilepath(packageGuid, packageCiMap,
                    configFile.getFilename(), rootDirName);
            if (saltFileNode == null) {
                configFile.setComparisonResult(FILE_COMP_DELETED);
                continue;
//                throw new PluginException(
//                        String.format("Diff configuration file %s does not exist.", configFile.getFilename()));
            }
            String filepath = configFile.getFilename();
            if (saltFileNode.getIsDir()) {
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

    private void processDiffConfFilesIfExistDiffConfFiles(SinglePackageQueryResultDto packageUpdateResult,
            Map<String, Object> packageCiMap, List<ConfigFileDto> newDiffConfFiles, List<String> oldDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs, List<DiffConfVariableInfoDto> diffConfVariables) {
        if (checkIfSameDiffConfFiles(newDiffConfFiles, oldDiffConfFiles)) {
            processDiffConfFilesIfSameDiffConfFiles(packageUpdateResult, packageCiMap, newDiffConfFiles,
                    oldDiffConfFiles, allCmdbDiffConfigs, diffConfVariables);

            return;
        } else {
            processDiffConfFilesIfModifiedDiffConfFiles(packageUpdateResult, packageCiMap, newDiffConfFiles,
                    oldDiffConfFiles, allCmdbDiffConfigs, diffConfVariables);
            return;
        }

    }

    private void processDiffConfFilesIfNotExistDiffConfFiles(SinglePackageQueryResultDto packageUpdateResult,
            Map<String, Object> packageCiMap, List<ConfigFileDto> newDiffConfFiles,
            List<CmdbDiffConfigDto> allCmdbDiffConfigs) {
        if (newDiffConfFiles == null || newDiffConfFiles.isEmpty()) {
            return;
        }

        String packageGuid = packageUpdateResult.getPackageId();
        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        String rootDirName = getDeployPackageRootDirName(packageCiMap);
        Set<String> configFileKeys = new HashSet<String>();
        for (ConfigFileDto configFile : newDiffConfFiles) {
            SaltFileNodeDto saltFileNode = getSaltFileNodeBySingleFilepath(packageGuid, packageCiMap,
                    configFile.getFilename(), rootDirName);
            if (saltFileNode == null) {
                configFile.setComparisonResult(FILE_COMP_DELETED);
                continue;
            }
            String filepath = configFile.getFilename();
            if (saltFileNode.getIsDir()) {
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

    private void updateConfigFilesToPackageCi(SinglePackageQueryResultDto packageUpdateResult,
            PackageConfigFilesUpdateRequestDto packageReqDto) {
        List<ConfigFileDto> newDiffConfFiles = packageReqDto.getDiffConfFile();
        String diffConfigFileStr = assembleDiffConfigFileString(newDiffConfFiles);

        Map<String, Object> packageUpdateParams = new HashMap<String, Object>();
        packageUpdateParams.put("guid", packageUpdateResult.getPackageId());
        packageUpdateParams.put("deploy_file_path", assembleFileItemsToString(packageReqDto.getDeployFilePath()));
        packageUpdateParams.put("start_file_path", assembleFileItemsToString(packageReqDto.getStartFilePath()));
        packageUpdateParams.put("stop_file_path", assembleFileItemsToString(packageReqDto.getStopFilePath()));
        packageUpdateParams.put("is_decompression", convertCmdbBooleanToString(packageReqDto.getIsDecompression()));
        packageUpdateParams.put("diff_conf_file", diffConfigFileStr);
        packageUpdateParams.put("baseline_package", packageReqDto.getBaselinePackage());

        this.updatePackageCi(packageUpdateParams);
    }

    private String convertCmdbBooleanToString(Boolean bool) {
        if (bool == null) {
            return null;
        }

        return String.valueOf(bool);
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
