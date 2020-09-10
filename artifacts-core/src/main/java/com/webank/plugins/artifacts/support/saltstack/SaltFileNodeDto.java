package com.webank.plugins.artifacts.support.saltstack;

import java.util.List;

public class SaltFileNodeDto {
    private String name;
    private String path;
    private boolean isDir;
    private String md5;
    private List<SaltFileNodeDto> fileNodes;
    
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
    public boolean isDir() {
        return isDir;
    }
    public void setDir(boolean isDir) {
        this.isDir = isDir;
    }
    public String getMd5() {
        return md5;
    }
    public void setMd5(String md5) {
        this.md5 = md5;
    }
    public List<SaltFileNodeDto> getFileNodes() {
        return fileNodes;
    }
    public void setFileNodes(List<SaltFileNodeDto> fileNodes) {
        this.fileNodes = fileNodes;
    }
}
