package com.webank.plugins.artifacts.dto;

import java.util.ArrayList;
import java.util.List;

public class FileQueryResultItemDto {

    private String name;
    private Boolean isDir;
    private String comparisonResult;
    private String md5;

    private List<FileQueryResultItemDto> children;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Boolean getIsDir() {
        return isDir;
    }

    public void setIsDir(Boolean isDir) {
        this.isDir = isDir;
    }

    public String getComparisonResult() {
        return comparisonResult;
    }

    public void setComparisonResult(String comparisonResult) {
        this.comparisonResult = comparisonResult;
    }

    public List<FileQueryResultItemDto> getChildren() {
        return children;
    }

    public void setChildren(List<FileQueryResultItemDto> children) {
        this.children = children;
    }

    public void addFileQueryResultItem(FileQueryResultItemDto item) {
        if (item == null) {
            return;
        }

        if (this.children == null) {
            this.children = new ArrayList<FileQueryResultItemDto>();
        }

        this.children.add(item);
    }
    
    public String getMd5() {
        return md5;
    }

    public void setMd5(String md5) {
        this.md5 = md5;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("[name=");
        builder.append(name);
        builder.append(", isDir=");
        builder.append(isDir);
        builder.append(", comparisonResult=");
        builder.append(comparisonResult);
        builder.append(", children=");
        builder.append(children);
        builder.append("]");
        return builder.toString();
    }

}
