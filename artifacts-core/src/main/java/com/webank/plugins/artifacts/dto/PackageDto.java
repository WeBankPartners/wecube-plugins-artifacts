package com.webank.plugins.artifacts.dto;

import java.util.List;

public class PackageDto {
    private List<String> configFilesWithPath;
    private String deployFile;
    private String startFile;
    private String stopFile;
    private String isDecompression;

    public List<String> getConfigFilesWithPath() {
        return configFilesWithPath;
    }

    public void setConfigFilesWithPath(List<String> configFilesWithPath) {
        this.configFilesWithPath = configFilesWithPath;
    }

    public String getDeployFile() {
        return deployFile;
    }

    public void setDeployFile(String deployFile) {
        this.deployFile = deployFile;
    }

    public String getStartFile() {
        return startFile;
    }

    public void setStartFile(String startFile) {
        this.startFile = startFile;
    }

    public String getStopFile() {
        return stopFile;
    }

    public void setStopFile(String stopFile) {
        this.stopFile = stopFile;
    }

    public String getIsDecompression() {
        return isDecompression;
    }

    public void setIsDecompression(String isDecompression) {
        this.isDecompression = isDecompression;
    }

}
