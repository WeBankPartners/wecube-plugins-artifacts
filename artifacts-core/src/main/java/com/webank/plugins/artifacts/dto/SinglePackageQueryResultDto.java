package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public class SinglePackageQueryResultDto {

    private String packageId;
    @JsonProperty("baseline_package")
    private String baselinePackage;

    @JsonProperty("is_decompression")
    private Boolean isDecompression;

    @JsonProperty("start_file_path")
    private List<ConfigFileDto> startFilePath = new ArrayList<>();
    @JsonProperty("stop_file_path")
    private List<ConfigFileDto> stopFilePath = new ArrayList<>();
    @JsonProperty("deploy_file_path")
    private List<ConfigFileDto> deployFilePath = new ArrayList<>();
    @JsonProperty("diff_conf_file")
    private List<ConfigFileDto> diffConfFile = new ArrayList<>();

    @JsonProperty("diff_conf_variable")
    private List<DiffConfVariableInfoDto> diffConfVariable = new ArrayList<>();

    public String getPackageId() {
        return packageId;
    }

    public void setPackageId(String packageId) {
        this.packageId = packageId;
    }

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

    public List<DiffConfVariableInfoDto> getDiffConfVariable() {
        return diffConfVariable;
    }

    public void setDiffConfVariable(List<DiffConfVariableInfoDto> diffConfVariable) {
        this.diffConfVariable = diffConfVariable;
    }

    public String getBaselinePackage() {
        return baselinePackage;
    }

    public void setBaselinePackage(String baselinePackage) {
        this.baselinePackage = baselinePackage;
    }

    public Boolean getIsDecompression() {
        return isDecompression;
    }

    public void setIsDecompression(Boolean isDecompression) {
        this.isDecompression = isDecompression;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("SinglePackageQueryResultDto [packageId=");
        builder.append(packageId);
        builder.append(", baselinePackage=");
        builder.append(baselinePackage);
        builder.append(", isDecompression=");
        builder.append(isDecompression);
        builder.append(", startFilePath=");
        builder.append(startFilePath);
        builder.append(", stopFilePath=");
        builder.append(stopFilePath);
        builder.append(", deployFilePath=");
        builder.append(deployFilePath);
        builder.append(", diffConfFile=");
        builder.append(diffConfFile);
        builder.append(", diffConfVariable=");
        builder.append(diffConfVariable);
        builder.append("]");
        return builder.toString();
    }

    

    
}
