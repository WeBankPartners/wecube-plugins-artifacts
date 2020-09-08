package com.webank.plugins.artifacts.dto;

public class ConfigKeyInfoDto {
    
    public static final String BOUND_YES = "Y";
    public static final String BOUND_NO = "N";

    private String line;
    private String key;
    private String type;
    
    private String diffConfigGuid;
    private String bound;//"Y","N"
    private String diffExpr; //JSON
    

    public String getLine() {
        return line;
    }

    public void setLine(String line) {
        this.line = line;
    }

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

    public String getBound() {
        return bound;
    }

    public void setBound(String bound) {
        this.bound = bound;
    }

    public String getDiffExpr() {
        return diffExpr;
    }

    public void setDiffExpr(String diffExpr) {
        this.diffExpr = diffExpr;
    }
    
    

}
