package com.webank.plugins.artifacts.dto;

public class PackageComparisionRequestDto {

    private String baselinePackage;

    public String getBaselinePackageId() {
        return baselinePackage;
    }

    public void setBaselinePackageId(String baselinePackage) {
        this.baselinePackage = baselinePackage;
    }

}
