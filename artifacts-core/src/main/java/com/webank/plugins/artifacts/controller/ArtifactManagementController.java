package com.webank.plugins.artifacts.controller;

import static com.google.common.collect.Lists.newArrayList;
import static com.webank.plugins.artifacts.domain.JsonResponse.*;
import static com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery.defaultQueryObject;
import static com.webank.plugins.artifacts.utils.BooleanUtils.isTrue;
import static org.apache.commons.lang3.StringUtils.isNotEmpty;

import java.io.*;
import java.net.URL;
import java.net.URLConnection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.servlet.http.HttpServletRequest;

import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.*;
import com.webank.plugins.artifacts.utils.Base64Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONException;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.webank.plugins.artifacts.commons.ApplicationProperties.CmdbDataProperties;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.constant.ArtifactsConstants;
import com.webank.plugins.artifacts.domain.JsonResponse;
import com.webank.plugins.artifacts.domain.PackageDomain;
import com.webank.plugins.artifacts.service.ArtifactService;
import com.webank.plugins.artifacts.support.cmdb.CmdbServiceV2Stub;

@RestController
public class ArtifactManagementController {

    private static final Logger logger = LoggerFactory.getLogger(ArtifactManagementController.class);
    @Autowired
    CmdbDataProperties cmdbDataProperties;

    @Autowired
    private CmdbServiceV2Stub cmdbServiceV2Stub;

    @Autowired
    private ArtifactService artifactService;

    @Autowired
    private ApplicationProperties applicationProperties;

    @GetMapping("/system-design-versions")
    @ResponseBody
    public JsonResponse getSystemDesignVersions() {
        try {
            return okayWithData(artifactService.getSystemDesignVersions());
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @GetMapping("/system-design-versions/{system-design-id}")
    @ResponseBody
    public JsonResponse getSystemDesignVersion(@PathVariable(value = "system-design-id") String systemDesignId) {
        try {
            return okayWithData(artifactService.getArtifactSystemDesignTree(systemDesignId));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/upload")
    @ResponseBody
    public JsonResponse uploadPackage(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestParam(value = "file", required = false) MultipartFile multipartFile, HttpServletRequest request) {
        try {
            File file = convertMultiPartToFile(multipartFile);
            String url = artifactService.uploadPackageToS3(file);
            return okayWithData(artifactService.savePackageToCmdb(file, unitDesignId, (String)request.getAttribute(ArtifactsConstants.UPLOAD_NAME), url, null));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/query")
    @ResponseBody
    public JsonResponse queryPackages(@PathVariable(value = "unit-design-id") String unitDesignId,
            @RequestBody PaginationQuery queryObject) {
        try {
            queryObject.addEqualsFilter("unit_design", unitDesignId);
            return okayWithData(cmdbServiceV2Stub.queryCiData(cmdbDataProperties.getCiTypeIdOfPackage(), queryObject));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/queryNexusDirectiry")
    @ResponseBody
    public JsonResponse queryNexusPackages(@PathVariable(value = "unit-design-id") String unitDesignId,
                                           @RequestBody PaginationQuery queryObject) {
        try {
            return okayWithData(artifactService.queryNexusDirectiry(artifactService.getArtifactPath(unitDesignId, queryObject)));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/uploadNexusPackage")
    @ResponseBody
    public JsonResponse uploadNexusPackage(@PathVariable(value = "unit-design-id") String unitDesignId,
                                      @RequestParam(value = "downloadUrl", required = false) String downloadUrl, HttpServletRequest request) {
        try {
             asyncUploadNexusPackageToS3(unitDesignId,downloadUrl,(String)request.getAttribute(ArtifactsConstants.UPLOAD_NAME));
             return okay();
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    private void asyncUploadNexusPackageToS3(String unitDesignId, String downloadUrl,String uploadName) {
        ExecutorService executor = Executors.newFixedThreadPool(1);
        String authorization = AuthorizationStorage.getIntance().get();
        executor.submit(new Runnable() {
            @Override
            public void run() {
                try {
                    logger.info("sync upload NEXUS package to S3 begin");
                    File file = convertNexusPackageToFile(downloadUrl,downloadUrl.substring(downloadUrl.lastIndexOf("/") + 1));
                    String url = artifactService.uploadPackageToS3(file);
                    artifactService.savePackageToCmdb(file, unitDesignId, uploadName, url, authorization);
                    logger.info("sync upload NEXUS package to S3 end");
                } catch (Exception e) {
                    logger.info("sync upload NEXUS package to S3 failed ,", e);
                }
            }
        });
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/deactive")
    @ResponseBody
    public JsonResponse deactivePackage(@PathVariable(value = "package-id") String packageId) {
        try {
            artifactService.deactive(packageId);
            return okay();
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/active")
    @ResponseBody
    public JsonResponse activePackage(@PathVariable(value = "package-id") String packageId) {
        try {
            artifactService.active(packageId);
            return okay();
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/files/query")
    @ResponseBody
    public JsonResponse getFiles(@PathVariable(value = "package-id") String packageId,
            @RequestBody Map<String, String> additionalProperties) {
        try {
            if (additionalProperties.get("currentDir") == null) {
                throw new PluginException("Field 'currentDir' is required.");
            }
            return okayWithData(artifactService.getCurrentDirs(packageId, additionalProperties.get("currentDir")));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/property-keys/query")
    @ResponseBody
    public JsonResponse getKeys(@PathVariable(value = "package-id") String packageId,
            @RequestBody Map<String, String> additionalProperties) {
        try {
            if (additionalProperties.get("filePath") == null) {
                throw new PluginException("Field 'filePath' is required.");
            }
            return okayWithData(artifactService.getPropertyKeys(packageId, additionalProperties.get("filePath")));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/save")
    @ResponseBody
    public JsonResponse saveConfigFiles(@PathVariable(value = "package-id") String packageId, @RequestBody PackageDomain packageDomain) {
        try {
            artifactService.saveConfigFiles(packageId, packageDomain);
            return okay();
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/enum/codes/diff-config/save")
    @ResponseBody
    public JsonResponse saveDiffConfigEnumCodes(@RequestBody CatCodeDto code) {
        try {
            artifactService.saveDiffConfigEnumCodes(code);
            return okay();
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @GetMapping("/enum/codes/diff-config/query")
    @ResponseBody
    public JsonResponse getDiffConfigEnumCodes() {
        try {
            return okayWithData(artifactService.getDiffConfigEnumCodes());
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @GetMapping("/getPackageCiTypeId")
    @ResponseBody
    public JsonResponse getPackageCiTypeId() {
        try {
            return okayWithData(cmdbDataProperties.getCiTypeIdOfPackage());
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    private File convertMultiPartToFile(MultipartFile multipartFile) {
        if (multipartFile == null) {
            return null;
        }

        File file = new File(multipartFile.getOriginalFilename());
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(multipartFile.getBytes());
        } catch (Exception e) {
            throw new PluginException("Fail to convert multipart file to file", e);
        }
        return file;
    }

    private File convertNexusPackageToFile(String downloadUrl,String fileName) {
        File file = new File(fileName);
        try {
            URL url = new URL(downloadUrl);
            URLConnection connection = url.openConnection();
            connection.setConnectTimeout(5 * 1000);
            connection.setRequestProperty("Authorization","Basic " + Base64Utils.getBASE64(applicationProperties.getArtifactsNexusUsername() + ":" + applicationProperties.getArtifactsNexusPassword()));
            InputStream inputStream = connection.getInputStream();
            byte[] byteArr = new byte[1024];
            int len;
            FileOutputStream fos = new FileOutputStream(file);
            while ((len = inputStream.read(byteArr)) != -1) {
                fos.write(byteArr, 0, len);
            }
            fos.close();
            inputStream.close();
        } catch (IOException e) {
            throw new PluginException("Fail to convert Nexus package to file", e);
        }
       return file;
    }


    @PostMapping("/ci/state/operate")
    public JsonResponse operateCiForState(@RequestBody List<OperateCiDto> ciIds, @RequestParam("operation") String operation) {
        try {
            return okayWithData(artifactService.operateState(ciIds, operation));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @GetMapping("/ci-types")
    @ResponseBody
    public JsonResponse getCiTypes(@RequestParam(name = "group-by", required = false) String groupBy, @RequestParam(name = "with-attributes", required = false) String withAttributes,
            @RequestParam(name = "status", required = false) String status) {
        try {
            return okayWithData(artifactService.getCiTypes(isTrue(withAttributes), status));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }

    @PostMapping("/ci-types/{ci-type-id}/ci-data/batch-delete")
    @ResponseBody
    public JsonResponse deleteCiData(@PathVariable(value = "ci-type-id") int ciTypeId, @RequestBody List<String> ciDataIds) {
        try {
            artifactService.deleteCiData(ciTypeId, ciDataIds);
            return okay();
        } catch (Exception e) {
            logger.error(e.getMessage(),e);
            return error("The parameter ciDataIds is wrong," + e.getMessage());
        }
    }

    @PostMapping("/enum/system/codes")
    @ResponseBody
    public JsonResponse querySystemEnumCodesWithRefResources(@RequestBody PaginationQuery queryObject) {
        try {
            return okayWithData(artifactService.querySystemEnumCodesWithRefResources(queryObject));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }
    
    @GetMapping("/ci-types/{ci-type-id}/references/by")
    @ResponseBody
    public JsonResponse getCiTypeReferenceBy(@PathVariable(value = "ci-type-id") int ciTypeId) {
        try {
            return okayWithData(artifactService.getCiTypeReferenceBy(ciTypeId));
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }
    
    @GetMapping("/ci-types/{ci-type-id}/attributes")
    @ResponseBody
    public JsonResponse getCiTypeAttributes(@PathVariable(value = "ci-type-id") int ciTypeId, @RequestParam(name = "accept-input-types", required = false) String acceptInputTypes) {
        try {
            if (isNotEmpty(acceptInputTypes)) {
                return okayWithData(cmdbServiceV2Stub.queryCiTypeAttributes(defaultQueryObject("ciTypeId", ciTypeId).addInFilter("inputType", newArrayList(acceptInputTypes.split(",")))));
            } else {
                return okayWithData(cmdbServiceV2Stub.getCiTypeAttributesByCiTypeId(ciTypeId));
            }
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }
    
    @GetMapping("/static-data/special-connector")
    @ResponseBody
    public JsonResponse getSpecialConnector() {
        try {
            return okayWithData(artifactService.getSpecialConnector());
        }catch (Exception e){
            logger.error(e.getMessage(),e);
            return error(e.getMessage());
        }
    }
}
