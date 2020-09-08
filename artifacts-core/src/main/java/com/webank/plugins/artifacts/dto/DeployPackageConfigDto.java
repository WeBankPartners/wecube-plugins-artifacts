package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class DeployPackageConfigDto {
    private String packageId;
    private String unitDesignId;
    
    private List<DeployConfigFileDto> deployConfigFiles = new ArrayList<DeployConfigFileDto>();

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

    public List<DeployConfigFileDto> getDeployConfigFiles() {
        return deployConfigFiles;
    }

    public void setDeployConfigFiles(List<DeployConfigFileDto> deployConfigFiles) {
        this.deployConfigFiles = deployConfigFiles;
    }

    public void addDeployConfigFile(DeployConfigFileDto dto){
        if(dto == null){
            return;
        }
        
        if(this.deployConfigFiles == null){
            this.deployConfigFiles = new ArrayList<DeployConfigFileDto>();
        }
        
        this.deployConfigFiles.add(dto);
    }
    

}
