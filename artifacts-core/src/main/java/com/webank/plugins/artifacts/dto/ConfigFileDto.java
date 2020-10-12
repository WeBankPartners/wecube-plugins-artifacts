package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class ConfigFileDto {
    private String filename;
    private String comparisonResult;
    private String md5;
    private Boolean isDir;

    private List<ConfigKeyInfoDto> configKeyInfos = new ArrayList<>();

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getComparisonResult() {
        return comparisonResult;
    }

    public void setComparisonResult(String comparisonResult) {
        this.comparisonResult = comparisonResult;
    }

    public List<ConfigKeyInfoDto> getConfigKeyInfos() {
        return configKeyInfos;
    }

    public void setConfigKeyInfos(List<ConfigKeyInfoDto> configKeyInfos) {
        this.configKeyInfos = configKeyInfos;
    }

    public void addConfigKeyInfo(ConfigKeyInfoDto dto) {
        if (dto == null) {
            return;
        }

        if (this.configKeyInfos == null) {
            this.configKeyInfos = new ArrayList<ConfigKeyInfoDto>();
        }

        this.configKeyInfos.add(dto);
    }

    public String getMd5() {
        return md5;
    }

    public void setMd5(String md5) {
        this.md5 = md5;
    }

    public Boolean getIsDir() {
        return isDir;
    }

    public void setIsDir(Boolean isDir) {
        this.isDir = isDir;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("ConfigFileDto [filename=");
        builder.append(filename);
        builder.append(", comparisonResult=");
        builder.append(comparisonResult);
        builder.append(", md5=");
        builder.append(md5);
        builder.append(", isDir=");
        builder.append(isDir);
        builder.append(", configKeyInfos=");
        builder.append(configKeyInfos);
        builder.append("]");
        return builder.toString();
    }
    
    

}
