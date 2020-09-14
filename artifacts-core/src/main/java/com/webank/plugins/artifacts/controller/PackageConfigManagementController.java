package com.webank.plugins.artifacts.controller;

import static com.webank.plugins.artifacts.dto.JsonResponse.okayWithData;
import static com.webank.plugins.artifacts.dto.JsonResponse.okay;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.webank.plugins.artifacts.dto.ConfigPackageDto;
import com.webank.plugins.artifacts.dto.DiffConfigurationUpdateDto;
import com.webank.plugins.artifacts.dto.FileQueryRequestDto;
import com.webank.plugins.artifacts.dto.FileQueryResultItemDto;
import com.webank.plugins.artifacts.dto.JsonResponse;
import com.webank.plugins.artifacts.dto.PackageComparisionRequestDto;
import com.webank.plugins.artifacts.dto.PackageComparisionResultDto;
import com.webank.plugins.artifacts.dto.PackageConfigFilesUpdateRequestDto;
import com.webank.plugins.artifacts.dto.SinglePackageQueryResultDto;
import com.webank.plugins.artifacts.service.ConfigFileManagementService;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;

@RestController
public class PackageConfigManagementController {

    @Autowired
    private ConfigFileManagementService configFileManagementService;
    
    @PostMapping("/artifacts/packages/wecmdb/entities/diff_configuration/update")
    public JsonResponse updateDiffConfiguration(List<DiffConfigurationUpdateDto> updateRequestDto) {
        configFileManagementService.updateDiffConfigurations(updateRequestDto);
        return okay();
    }
    
    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/files/query")
    public JsonResponse queryPackageFiles(@PathVariable(value = "package-id") String packageId,
            @RequestBody FileQueryRequestDto fileQueryRequestDto) {
        List<FileQueryResultItemDto> results =  configFileManagementService.queryDeployConfigFiles(packageId,
                 fileQueryRequestDto);
        return okayWithData(results);
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
            @PathVariable(value = "package-id") String packageId,
            @RequestBody PackageComparisionRequestDto comparisonReqDto) {
        PackageComparisionResultDto result = configFileManagementService.packageComparision(unitDesignId, packageId,
                comparisonReqDto);
        return okayWithData(result);
    }

    @PostMapping("/unit-designs/{unit-design-id}/packages/{package-id}/update")
    public JsonResponse updateConfigFilesOfPackage(@PathVariable(value = "unit-design-id") String unitDesignId,
            @PathVariable(value = "package-id") String packageId, @RequestBody PackageConfigFilesUpdateRequestDto packageDomain) {
        SinglePackageQueryResultDto result = configFileManagementService.updateConfigFilesOfPackage(unitDesignId, packageId,
                packageDomain);
        return okayWithData(result);
    }
}
