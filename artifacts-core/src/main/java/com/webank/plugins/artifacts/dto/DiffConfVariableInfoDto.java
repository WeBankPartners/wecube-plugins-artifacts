package com.webank.plugins.artifacts.dto;

public class DiffConfVariableInfoDto {
    private String key;
    private String type;
    private String diffConfigGuid;
    private Boolean bound;
    private String diffExpr; // JSON

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getDiffConfigGuid() {
        return diffConfigGuid;
    }

    public void setDiffConfigGuid(String diffConfigGuid) {
        this.diffConfigGuid = diffConfigGuid;
    }

    public Boolean getBound() {
        return bound;
    }

    public void setBound(Boolean bound) {
        this.bound = bound;
    }

    public String getDiffExpr() {
        return diffExpr;
    }

    public void setDiffExpr(String diffExpr) {
        this.diffExpr = diffExpr;
    }

}
