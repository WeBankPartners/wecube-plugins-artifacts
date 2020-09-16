package com.webank.plugins.artifacts.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class DiffConfigurationUpdateDto {
    
    private String id;
    
    @JsonProperty("variable_value")
    private String diffExpr;
    public String getId() {
        return id;
    }
    public void setId(String id) {
        this.id = id;
    }
    public String getDiffExpr() {
        return diffExpr;
    }
    public void setDiffExpr(String diffExpr) {
        this.diffExpr = diffExpr;
    }
    
    

}
