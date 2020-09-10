package com.webank.plugins.artifacts.controller;

import static com.google.common.collect.Lists.newArrayList;
import static com.webank.plugins.artifacts.dto.JsonResponse.okay;
import static com.webank.plugins.artifacts.dto.JsonResponse.okayWithData;
import static com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.defaultQueryObject;
import static com.webank.plugins.artifacts.utils.BooleanUtils.isTrue;
import static org.apache.commons.lang3.StringUtils.isNotEmpty;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.List;
import java.util.Map;

import javax.servlet.http.HttpServletRequest;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.webank.plugins.artifacts.commons.ApplicationProperties.CmdbDataProperties;
import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.constant.ArtifactsConstants;
import com.webank.plugins.artifacts.dto.ConfigPackageDto;
import com.webank.plugins.artifacts.dto.FileQueryRequestDto;
import com.webank.plugins.artifacts.dto.JsonResponse;
import com.webank.plugins.artifacts.dto.PackageComparisionRequestDto;
import com.webank.plugins.artifacts.dto.PackageComparisionResultDto;
import com.webank.plugins.artifacts.dto.PackageDto;
import com.webank.plugins.artifacts.dto.SinglePackageQueryResultDto;
import com.webank.plugins.artifacts.service.ArtifactService;
import com.webank.plugins.artifacts.service.ConfigFileManagementService;
import com.webank.plugins.artifacts.service.NexusArtifactManagementService;
import com.webank.plugins.artifacts.support.cmdb.CmdbServiceV2Stub;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.CatCodeDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.OperateCiDto;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;

@RestController
public class ArtifactManagementController {

    private static final Logger logger = LoggerFactory.getLogger(ArtifactManagementController.class);
    @Autowired
    private CmdbDataProperties cmdbDataProperties;

    @Autowired
    private CmdbServiceV2Stub cmdbServiceV2Stub;

    @Autowired
    private ArtifactService artifactService;

    @Autowired
    private NexusArtifactManagementService nexusArtifactManagementService;

    @Autowired
    private ConfigFileManagementService configFileManagementService;
    
    @GetMapping("/system-design-versions")
    public JsonResponse getSystemDesignVersions() {
        return okayWithData(artifactService.getSystemDesignVersions());
    }

    @GetMapping("/system-design-versions/{system-design-id}")
    public JsonResponse getSystemDesignVersion(@PathVariable(value = "system-design-id") String systemDesignId) {
        return okayWithData(artifactService.getArtifactSystemDesignTree(systemDesignId));

    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/upload")
    public JsonResponse uploadPackage(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestParam(value = "file", required = false) MultipartFile multipartFile, HttpServletRequest request) {
        File file = convertMultiPartToFile(multipartFile);
        String url = artifactService.uploadPackageToS3(file);
        return okayWithData(artifactService.savePackageToCmdb(file, unitDesignId,
                (String) request.getAttribute(ArtifactsConstants.UPLOAD_NAME), url, null));

    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/query")
    public JsonResponse queryPackages(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestBody PaginationQuery queryObject) {
        PaginationQueryResult<Map<String, Object>> results = configFileManagementService
                .queryDeployPackages(unitDesignId, queryObject);
        return okayWithData(results);
    }

    @GetMapping("/unit-designs/{unit-design-id}/packages/{package-id}/query")
    public JsonResponse querySinglePackage(@PathVariable(value = "unit-design-id") String unitDesignId,
            @PathVariable(value = "package-id") String packageId) {
        SinglePackageQueryResultDto result = configFileManagementService.querySinglePackage(unitDesignId, packageId);
        return okayWithData(result);
    }
    
    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/comparison")
    public JsonResponse packageComparision(@PathVariable(value = "unit-design-id") String unitDesignId,
            @PathVariable(value = "package-id") String packageId, @RequestBody PackageComparisionRequestDto comparisonReqDto) {
        PackageComparisionResultDto result = configFileManagementService.packageComparision(unitDesignId, packageId, comparisonReqDto);
        return okayWithData(result);
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/queryNexusDirectiry")
    public JsonResponse queryNexusPackages(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestBody PaginationQuery queryObject) {
        return okayWithData(nexusArtifactManagementService.queryNexusDirectory(unitDesignId, queryObject));
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/uploadNexusPackage")
    public JsonResponse uploadNexusPackage(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestParam(value = "downloadUrl", required = false) String downloadUrl, HttpServletRequest request) {
        nexusArtifactManagementService.asyncUploadNexusPackageToS3(unitDesignId, downloadUrl,
                (String) request.getAttribute(ArtifactsConstants.UPLOAD_NAME));
        return okay();
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/deactive")
    public JsonResponse deactivePackage(@PathVariable(value = "package-id") String packageId) {
        artifactService.deactive(packageId);
        return okay();
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/active")
    public JsonResponse activePackage(@PathVariable(value = "package-id") String packageId) {
        artifactService.active(packageId);
        return okay();
    }

//    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/files/query")
//    public JsonResponse getFiles(@PathVariable(value = "package-id") String packageId,
//            @RequestBody FileQueryRequestDto fileQueryRequestDto) {
////        if (additionalProperties.get("currentDir") == null) {
////            throw new PluginException("3000", "Field 'currentDir' is required.");
////        }
//        return okayWithData(artifactService.getCurrentDirs(packageId, additionalProperties.get("currentDir")));
//        
////        //TODO
////        return null;
//    }
    
    
    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/files/query")
    public JsonResponse getFiles(@PathVariable(value = "package-id") String packageId,
            @RequestBody Map<String, String> additionalProperties) {
//        if (additionalProperties.get("currentDir") == null) {
//            throw new PluginException("3000", "Field 'currentDir' is required.");
//        }
        return okayWithData(artifactService.getCurrentDirs(packageId, additionalProperties.get("currentDir")));
        
//        //TODO
//        return null;
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/property-keys/query")
    public JsonResponse getKeys(@PathVariable(value = "package-id") String packageId,
            @RequestBody Map<String, String> additionalProperties) {
        if (additionalProperties.get("filePath") == null) {
            throw new PluginException("3001", "Field 'filePath' is required.");
        }
        return okayWithData(artifactService.getPropertyKeys(packageId, additionalProperties.get("filePath")));
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/save")
    public JsonResponse saveConfigFiles(@PathVariable(value = "unit-design-id") String unitDesignId,
            @PathVariable(value = "package-id") String packageId, @RequestBody PackageDto packageDomain) {
        ConfigPackageDto result = configFileManagementService.saveConfigFiles(unitDesignId, packageId,
                packageDomain);
        return okayWithData(result);
    }

    @PostMapping("/enum/codes/diff-config/save")
    public JsonResponse saveDiffConfigEnumCodes(@RequestBody CatCodeDto code) {
        artifactService.saveDiffConfigEnumCodes(code);
        return okay();
    }

    @GetMapping("/enum/codes/diff-config/query")
    public JsonResponse getDiffConfigEnumCodes() {
        return okayWithData(artifactService.getDiffConfigEnumCodes());
    }

    @GetMapping("/getPackageCiTypeId")
    public JsonResponse getPackageCiTypeId() {
        return okayWithData(cmdbDataProperties.getCiTypeIdOfPackage());
    }

    @PostMapping("/ci/state/operate")
    public JsonResponse operateCiForState(@RequestBody List<OperateCiDto> ciIds,
            @RequestParam("operation") String operation) {
        return okayWithData(artifactService.operateState(ciIds, operation));
    }

    @GetMapping("/ci-types")
    public JsonResponse getCiTypes(@RequestParam(name = "group-by", required = false) String groupBy,
            @RequestParam(name = "with-attributes", required = false) String withAttributes,
            @RequestParam(name = "status", required = false) String status) {
        return okayWithData(artifactService.getCiTypes(isTrue(withAttributes), status));
    }

    @PostMapping("/ci-types/{ci-type-id}/ci-data/batch-delete")
    public JsonResponse deleteCiData(@PathVariable(value = "ci-type-id") int ciTypeId,
            @RequestBody List<String> ciDataIds) {
        artifactService.deleteCiData(ciTypeId, ciDataIds);
        return okay();
    }

    @PostMapping("/enum/system/codes")
    public JsonResponse querySystemEnumCodesWithRefResources(@RequestBody PaginationQuery queryObject) {
        return okayWithData(artifactService.querySystemEnumCodesWithRefResources(queryObject));
    }

    @GetMapping("/ci-types/{ci-type-id}/references/by")
    public JsonResponse getCiTypeReferenceBy(@PathVariable(value = "ci-type-id") int ciTypeId) {
        return okayWithData(artifactService.getCiTypeReferenceBy(ciTypeId));
    }

    @GetMapping("/ci-types/{ci-type-id}/attributes")
    public JsonResponse getCiTypeAttributes(@PathVariable(value = "ci-type-id") int ciTypeId,
            @RequestParam(name = "accept-input-types", required = false) String acceptInputTypes) {
        if (isNotEmpty(acceptInputTypes)) {
            return okayWithData(cmdbServiceV2Stub.queryCiTypeAttributes(defaultQueryObject("ciTypeId", ciTypeId)
                    .addInFilter("inputType", newArrayList(acceptInputTypes.split(",")))));
        } else {
            return okayWithData(cmdbServiceV2Stub.getCiTypeAttributesByCiTypeId(ciTypeId));
        }
    }

    @GetMapping("/static-data/special-connector")
    public JsonResponse getSpecialConnector() {
        return okayWithData(artifactService.getSpecialConnector());
    }

    private File convertMultiPartToFile(MultipartFile multipartFile) {
        if (multipartFile == null) {
            return null;
        }

        File file = new File(multipartFile.getOriginalFilename());
        try (FileOutputStream fos = new FileOutputStream(file)) {
            byte[] buf = new byte[1024];
            int len = 0;

            InputStream is = multipartFile.getInputStream();
            while ((len = is.read(buf)) != -1) {
                fos.write(buf, 0, len);
            }

            // fos.write(multipartFile.getBytes());
        } catch (Exception e) {
            logger.error("errors while convert multipart file.", e);
            throw new PluginException("3002", "Failed to convert multipart file to file.");
        }
        return file;
    }
}
