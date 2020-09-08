package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class DeployConfigFileDto {
    private String guid;
    private String filePath;
    
    private List<ConfigKeyInfoDto> configKeyInfos = new ArrayList<ConfigKeyInfoDto>();

    public String getGuid() {
        return guid;
    }

    public void setGuid(String guid) {
        this.guid = guid;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
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
