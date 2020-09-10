package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class ConfigFileDto {
    private String filename;
    private String comparisonResult;
    
    private List<ConfigKeyInfoDto> configKeyInfos;
    
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
    
    public void addConfigKeyInfo(ConfigKeyInfoDto dto){
        if(dto == null){
            return;
        }
        
        if(this.configKeyInfos == null){
            this.configKeyInfos = new ArrayList<ConfigKeyInfoDto>();
        }
        
        this.configKeyInfos.add(dto);
    }

}
