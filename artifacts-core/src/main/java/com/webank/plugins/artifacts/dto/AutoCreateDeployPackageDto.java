package com.webank.plugins.artifacts.dto;

public class AutoCreateDeployPackageDto {

    private String nexusUrl;
    private String baselinePackage;
    private String startFilePath;
    private String stopFilePath;
    private String deployFilePath;
    private String diffConfFile;
    
    public String getNexusUrl() {
        return nexusUrl;
    }
    public void setNexusUrl(String nexusUrl) {
        this.nexusUrl = nexusUrl;
    }
    public String getBaselinePackage() {
        return baselinePackage;
    }
    public void setBaselinePackage(String baselinePackage) {
        this.baselinePackage = baselinePackage;
    }
    public String getStartFilePath() {
        return startFilePath;
    }
    public void setStartFilePath(String startFilePath) {
        this.startFilePath = startFilePath;
    }
    public String getStopFilePath() {
        return stopFilePath;
    }
    public void setStopFilePath(String stopFilePath) {
        this.stopFilePath = stopFilePath;
    }
    public String getDeployFilePath() {
        return deployFilePath;
    }
    public void setDeployFilePath(String deployFilePath) {
        this.deployFilePath = deployFilePath;
    }
    public String getDiffConfFile() {
        return diffConfFile;
    }
    public void setDiffConfFile(String diffConfFile) {
        this.diffConfFile = diffConfFile;
    }
    
    
}
