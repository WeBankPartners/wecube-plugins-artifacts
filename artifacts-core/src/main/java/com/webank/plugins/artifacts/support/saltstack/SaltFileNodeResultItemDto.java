package com.webank.plugins.artifacts.support.saltstack;

import java.util.List;

public class SaltFileNodeResultItemDto {
    
    private String errorCode;
    private String errorMessage;
    private List<SaltFileNodeDto> files;
    
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
    public List<SaltFileNodeDto> getFiles() {
        return files;
    }
    public void setFiles(List<SaltFileNodeDto> files) {
        this.files = files;
    }
    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("[errorCode=");
        builder.append(errorCode);
        builder.append(", errorMessage=");
        builder.append(errorMessage);
        builder.append(", files=");
        builder.append(files);
        builder.append("]");
        return builder.toString();
    }
    
    

}
