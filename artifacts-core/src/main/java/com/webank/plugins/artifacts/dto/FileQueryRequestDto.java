package com.webank.plugins.artifacts.dto;

import java.util.List;

public class FileQueryRequestDto {
    private String baselinePackage;//nullable
    private List<String> fileList; //empty means root

    public String getBaselinePackage() {
        return baselinePackage;
    }

    public void setBaselinePackage(String baselinePackage) {
        this.baselinePackage = baselinePackage;
    }

    public List<String> getFileList() {
        return fileList;
    }

    public void setFileList(List<String> fileList) {
        this.fileList = fileList;
    }

}
