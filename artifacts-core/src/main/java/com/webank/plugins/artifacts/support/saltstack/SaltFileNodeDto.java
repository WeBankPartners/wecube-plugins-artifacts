package com.webank.plugins.artifacts.support.saltstack;

import com.fasterxml.jackson.annotation.JsonProperty;

public class SaltFileNodeDto {
    private String name;
    private String path;
    @JsonProperty("isDir")
    private Boolean isDir;
    private String md5;
    
    public String getName() {
        return name;
    }
    public void setName(String name) {
        this.name = name;
    }
    public String getPath() {
        return path;
    }
    public void setPath(String path) {
        this.path = path;
    }
    public Boolean getIsDir() {
        return isDir;
    }
    public void setDir(Boolean isDir) {
        this.isDir = isDir;
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
        builder.append(", path=");
        builder.append(path);
        builder.append(", isDir=");
        builder.append(isDir);
        builder.append(", md5=");
        builder.append(md5);
        builder.append("]");
        return builder.toString();
    }
    
    
}
