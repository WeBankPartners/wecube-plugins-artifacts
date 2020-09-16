package com.webank.plugins.artifacts.support.saltstack;

public class SaltConfigKeyInfoDto {
    private String line;
    private String key;
    private String type;

    private String sourceFilePath;

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

    public String getSourceFilePath() {
        return sourceFilePath;
    }

    public void setSourceFilePath(String sourceFilePath) {
        this.sourceFilePath = sourceFilePath;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("SaltConfigKeyInfoDto [line=");
        builder.append(line);
        builder.append(", key=");
        builder.append(key);
        builder.append(", type=");
        builder.append(type);
        builder.append(", sourceFilePath=");
        builder.append(sourceFilePath);
        builder.append("]");
        return builder.toString();
    }
    
    

}
