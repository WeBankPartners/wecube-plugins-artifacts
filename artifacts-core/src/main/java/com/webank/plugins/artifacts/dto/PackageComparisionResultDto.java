package com.webank.plugins.artifacts.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public class PackageComparisionResultDto {
    @JsonProperty("start_file_path")
    private List<ConfigFileDto> startFilePath;
    @JsonProperty("stop_file_path")
    private List<ConfigFileDto> stopFilePath;
    @JsonProperty("deploy_file_path")
    private List<ConfigFileDto> deployFilePath;
    @JsonProperty("diff_conf_file")
    private List<ConfigFileDto> diffConfFile;
    
    public List<ConfigFileDto> getStartFilePath() {
        return startFilePath;
    }
    public void setStartFilePath(List<ConfigFileDto> startFilePath) {
        this.startFilePath = startFilePath;
    }
    public List<ConfigFileDto> getStopFilePath() {
        return stopFilePath;
    }
    public void setStopFilePath(List<ConfigFileDto> stopFilePath) {
        this.stopFilePath = stopFilePath;
    }
    public List<ConfigFileDto> getDeployFilePath() {
        return deployFilePath;
    }
    public void setDeployFilePath(List<ConfigFileDto> deployFilePath) {
        this.deployFilePath = deployFilePath;
    }
    public List<ConfigFileDto> getDiffConfFile() {
        return diffConfFile;
    }
    public void setDiffConfFile(List<ConfigFileDto> diffConfFile) {
        this.diffConfFile = diffConfFile;
    }
    
    
}
