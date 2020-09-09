package com.webank.plugins.artifacts.support.saltstack;

public class SaltConfigKeyInfoDto {
    private String line;
    private String key;
    private String type;
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
    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("[line=");
        builder.append(line);
        builder.append(", key=");
        builder.append(key);
        builder.append(", type=");
        builder.append(type);
        builder.append("]");
        return builder.toString();
    }
    
    
}
