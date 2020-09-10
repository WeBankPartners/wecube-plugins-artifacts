package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class ConfigPackageDto {
    private String packageId;
    private String unitDesignId;
    
    private List<ConfigFileDto> deployConfigFiles = new ArrayList<ConfigFileDto>();

    public String getPackageId() {
        return packageId;
    }

    public void setPackageId(String packageId) {
        this.packageId = packageId;
    }

    public String getUnitDesignId() {
        return unitDesignId;
    }

    public void setUnitDesignId(String unitDesignId) {
        this.unitDesignId = unitDesignId;
    }

    public List<ConfigFileDto> getDeployConfigFiles() {
        return deployConfigFiles;
    }

    public void setDeployConfigFiles(List<ConfigFileDto> deployConfigFiles) {
        this.deployConfigFiles = deployConfigFiles;
    }

    public void addDeployConfigFile(ConfigFileDto dto){
        if(dto == null){
            return;
        }
        
        if(this.deployConfigFiles == null){
            this.deployConfigFiles = new ArrayList<ConfigFileDto>();
        }
        
        this.deployConfigFiles.add(dto);
    }
    

}
