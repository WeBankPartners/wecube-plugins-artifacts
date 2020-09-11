package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
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
import com.webank.plugins.artifacts.dto.ConfigPackageDto;
import com.webank.plugins.artifacts.dto.DiffConfVariableInfoDto;
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
import com.webank.plugins.artifacts.support.saltstack.SaltstackRequest.DefaultSaltstackRequest;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;

@Service
public class ConfigFileManagementService extends AbstractArtifactService {
    private static final Logger log = LoggerFactory.getLogger(ConfigFileManagementService.class);

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
            log.info("file list is empty and adding root as default");
            String rootDirName = getDeployPackageRootDir(packageCiMap);
            filePathList.add(rootDirName);
        } else {
            filePathList.addAll(inputFilePathList);
        }

        List<FileQueryResultItemDto> fileQueryResultItems = doQueryDeployConfigFiles(packageCiGuid, filePathList,
                packageCiMap);

        if (baselinePackageCiMap != null) {
            List<FileQueryResultItemDto> baselinePackageFileQueryResultItems = doQueryDeployConfigFiles(
                    baselinePackageGuid, filePathList, baselinePackageCiMap);
            doExecuteFileQueryComparison(fileQueryResultItems, baselinePackageFileQueryResultItems);

            // TODO deleted
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
            log.info("baselinePackageObj:{}", baselinePackageCiMap.getClass().getName());
            // String baselinePackageGuid = (String)
            // packageCiMap.get("baseline_package");
            baselinePackageGuid = (String) baselinePackageCiMap.get("guid");
        }

        SinglePackageQueryResultDto result = new SinglePackageQueryResultDto();
        result.setPackageId(packageId);
        result.setBaselinePackage(baselinePackageGuid);
        result.setIsCompress(null);// TODO

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
            baselineResult.setIsCompress(null);// TODO

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

        List<DiffConfVariableInfoDto> diffConfVariables = new ArrayList<DiffConfVariableInfoDto>();
        for (String diffConfigKey : allDiffConfigKeys) {
            CmdbDiffConfigDto cmdbDiffConfig = findoutFromCmdbDiffConfigsByKey(diffConfigKey, allCmdbDiffConfigs);
            if (cmdbDiffConfig == null) {
                log.info("Cannot find cmdb diff config key:{}", diffConfigKey);
                continue;
            }

            DiffConfVariableInfoDto diffVarInfo = new DiffConfVariableInfoDto();
            diffVarInfo.setBound(false);// TODO
            diffVarInfo.setDiffConfigGuid(cmdbDiffConfig.getGuid());
            diffVarInfo.setDiffExpr(cmdbDiffConfig.getDiffExpr());
            diffVarInfo.setKey(cmdbDiffConfig.getKey());

            diffConfVariables.add(diffVarInfo);
        }

        result.setDiffConfVariable(diffConfVariables);

        return result;
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

        log.info("filePathString:{}", filePathString);
        String[] fileStringParts = filePathString.split("\\|");
        for (String fileStringPart : fileStringParts) {
            ConfigFileDto fileDto = new ConfigFileDto();
            fileDto.setFilename(fileStringPart);

            files.add(fileDto);

            log.info("add file:{}", fileDto);
        }

        return files;
    }

    public ConfigPackageDto updateConfigFilesOfPackage(String unitDesignId, String packageId,
            PackageConfigFilesUpdateRequestDto packageReqDto) {
        String diffConfigFileStr = String.join("|", packageReqDto.getDiffConfFile().stream().map(dto -> {
            return dto.getFilename();
        }).collect(Collectors.toList()));

        // TODO
        // String files = String.join("|", packageDto.getConfigFilesWithPath());
        Map<String, Object> packageUpdateParams = new HashMap<String, Object>();
        packageUpdateParams.put("guid", packageId);
        packageUpdateParams.put("deploy_file_path", getExepectedFileName(packageReqDto.getDeployFilePath()));
        packageUpdateParams.put("start_file_path", getExepectedFileName(packageReqDto.getStartFilePath()));
        packageUpdateParams.put("stop_file_path", getExepectedFileName(packageReqDto.getStopFilePath()));
        packageUpdateParams.put("is_decompression", packageReqDto.getIsDecompression());
        packageUpdateParams.put("diff_conf_file", diffConfigFileStr);

        // Map<String, Object> pkg = ImmutableMap.<String, Object>builder() //
        // .put("guid", packageId) //
        // .put("deploy_file_path", packageDto.getDeployFile()) //
        // .put("start_file_path", packageDto.getStartFile()) //
        // .put("stop_file_path", packageDto.getStopFile()) //
        // .put("diff_conf_file", files) //
        // .put("is_decompression", packageDto.getIsDecompression()) //
        // .build();
        cmdbServiceV2Stub.updateCiData(cmdbDataProperties.getCiTypeIdOfPackage(), packageUpdateParams);

        ConfigPackageDto result = new ConfigPackageDto();
        result.setPackageId(packageId);
        result.setUnitDesignId(unitDesignId);

        String s3EndpointOfPackageId = retrieveS3EndpointWithKeyByPackageId(packageId);

        // query keys by file
        // for (String filePath : packageDto.getConfigFilesWithPath()) {
        // log.info("try to calculate filepath:{}", filePath);
        // ConfigFileDto deployConfigFile = calculatePropertyKeys(packageId,
        // filePath, s3EndpointOfPackageId);
        // result.addDeployConfigFile(deployConfigFile);
        // }

        // processDiffConfigurations(unitDesignId, packageId, result);

        return result;
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

        log.info("SaltConfigFileDto size:{}", saltConfigFileDtos.size());
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
        for (FileQueryResultItemDto item : fileQueryResultItems) {
            FileQueryResultItemDto baselineItem = pickoutFromFileQueryResultItems(item.getPath(),
                    baselinePackageFileQueryResultItems);
            if (baselineItem == null) {
                item.setComparisonResult(FILE_COMP_NEW);
            } else {
                if (item.getIsDir()) {
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
    }

    private FileQueryResultItemDto pickoutFromFileQueryResultItems(String path,
            List<FileQueryResultItemDto> baselinePackageFileQueryResultItems) {
        if (baselinePackageFileQueryResultItems == null || baselinePackageFileQueryResultItems.isEmpty()) {
            return null;
        }
        for (FileQueryResultItemDto item : baselinePackageFileQueryResultItems) {
            if (path.equals(item.getPath())) {
                return item;
            }

            FileQueryResultItemDto child = pickoutFromFileQueryResultItems(path, item.getChildren());
            if (child != null) {
                return child;
            }
        }

        return null;
    }

    private String getDeployPackageRootDir(Map<String, Object> packageCiMap) {
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs("", packageEndpoint);
        return saltFileNodes.get(0).getName();
    }

    private List<FileQueryResultItemDto> doQueryDeployConfigFiles(String packageCiGuid, List<String> filePathList,
            Map<String, Object> packageCiMap) {
        List<FileQueryResultItemDto> resultItemDtos = new ArrayList<FileQueryResultItemDto>();
        String rootDirName = getDeployPackageRootDir(packageCiMap);
        String packageEndpoint = retrieveS3EndpointWithKeyByPackageCiMap(packageCiMap);
        for (String filePath : filePathList) {
            FileQueryResultItemDto resultItemDto = handleSingleFilePath(packageCiGuid, filePath, packageCiMap,
                    packageEndpoint, rootDirName);

            resultItemDtos.add(resultItemDto);
        }
        return resultItemDtos;
    }

    private FileQueryResultItemDto handleSingleFilePath(String packageCiGuid, String filePath,
            Map<String, Object> packageCiMap, String packageEndpoint, String rootDirName) {

        log.info("to process filePath:{}", filePath);
        String rawBaseName = filePath;
        if (rawBaseName.indexOf("/") > 0) {
            rawBaseName = rawBaseName.substring(0, rawBaseName.lastIndexOf("/"));
        }

        if (!filePath.startsWith(rootDirName)) {
            if (filePath.startsWith("/")) {
                log.info("not start with slash:{}", filePath);
                filePath = rootDirName + filePath;
            } else {
                filePath = rootDirName + "/" + filePath;
            }
        }

        String baseDirName = filePath.substring(0, filePath.lastIndexOf("/"));
        String fileName = filePath.substring(filePath.lastIndexOf("/") + 1);
        FileQueryResultItemDto resultItemDto = new FileQueryResultItemDto();
        resultItemDto.setName(rawBaseName);
        resultItemDto.setPath(baseDirName);
        resultItemDto.setIsDir(true);
        resultItemDto.setComparisonResult(null);

        List<SaltFileNodeDto> saltFileNodes = listFilesOfCurrentDirs(baseDirName, packageEndpoint);

        for (SaltFileNodeDto saltFileNode : saltFileNodes) {
            FileQueryResultItemDto childResultItemDto = null;
            if (fileName.equals(saltFileNode.getName()) && saltFileNode.getIsDir()) {
                childResultItemDto = new FileQueryResultItemDto();
                childResultItemDto.setComparisonResult(null);
                childResultItemDto.setIsDir(true);
                childResultItemDto.setMd5(saltFileNode.getMd5());
                childResultItemDto.setName(fileName);
                childResultItemDto.setPath(filePath);

                List<SaltFileNodeDto> childSaltFileNodes = listFilesOfCurrentDirs(filePath, packageEndpoint);
                for (SaltFileNodeDto childSaltFileNode : childSaltFileNodes) {
                    String childFilePath = filePath + "/" + childSaltFileNode.getName();
                    FileQueryResultItemDto grandResultItemDto = convertToFileQueryResultItemDto(childSaltFileNode,
                            childFilePath);
                    childResultItemDto.addFileQueryResultItem(grandResultItemDto);
                }
            } else {
                childResultItemDto = convertToFileQueryResultItemDto(saltFileNode, filePath);
            }
            resultItemDto.addFileQueryResultItem(childResultItemDto);
        }

        return resultItemDto;
    }

    private FileQueryResultItemDto convertToFileQueryResultItemDto(SaltFileNodeDto saltFileNodeDto, String filePath) {
        FileQueryResultItemDto dto = new FileQueryResultItemDto();
        dto.setComparisonResult(null);
        dto.setIsDir(saltFileNodeDto.getIsDir());
        dto.setName(saltFileNodeDto.getName());
        dto.setMd5(saltFileNodeDto.getMd5());
        dto.setPath(filePath);

        return dto;
    }
}
