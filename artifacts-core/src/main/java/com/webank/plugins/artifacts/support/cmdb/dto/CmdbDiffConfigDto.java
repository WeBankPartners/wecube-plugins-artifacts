package com.webank.plugins.artifacts.support.cmdb.dto;

public class CmdbDiffConfigDto {
    private String guid;
    private String key;
    private String diffExpr;
    private String displayName;

    public String getGuid() {
        return guid;
    }

    public void setGuid(String guid) {
        this.guid = guid;
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getDiffExpr() {
        return diffExpr;
    }

    public void setDiffExpr(String diffExpr) {
        this.diffExpr = diffExpr;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

}
