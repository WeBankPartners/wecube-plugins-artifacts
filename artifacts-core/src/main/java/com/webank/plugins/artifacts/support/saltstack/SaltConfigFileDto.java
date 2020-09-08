package com.webank.plugins.artifacts.support.saltstack;

import java.util.ArrayList;
import java.util.List;

public class SaltConfigFileDto {
    private String errorCode;
    private String errorMessage;
    private String filePath;

    private List<SaltConfigKeyInfoDto> configKeyInfos = new ArrayList<SaltConfigKeyInfoDto>();

    public String getErrorCode() {
        return errorCode;
    }

    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public List<SaltConfigKeyInfoDto> getConfigKeyInfos() {
        return configKeyInfos;
    }

    public void setConfigKeyInfos(List<SaltConfigKeyInfoDto> configKeyInfos) {
        this.configKeyInfos = configKeyInfos;
    }
    
    

}
