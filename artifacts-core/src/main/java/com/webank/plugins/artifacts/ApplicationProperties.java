package com.webank.plugins.artifacts;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "plugins")
public class ApplicationProperties {

    private String packageName;
    private String wecmdbServerUrl;
    private Map<String, String> customHeaders = new LinkedHashMap<>();
    private Set<String> sensitiveHeaders = null;

    public String getPackageName() {
        return packageName;
    }

    public void setPackageName(String packageName) {
        this.packageName = packageName;
    }

    public String getWecmdbServerUrl() {
        return wecmdbServerUrl;
    }

    public void setWecmdbServerUrl(String wecmdbServerUrl) {
        this.wecmdbServerUrl = wecmdbServerUrl;
    }

    public Map<String, String> getCustomHeaders() {
        return customHeaders;
    }

    public void setCustomHeaders(Map<String, String> customHeaders) {
        this.customHeaders = customHeaders;
    }

    public Set<String> getSensitiveHeaders() {
        return sensitiveHeaders;
    }

    public void setSensitiveHeaders(Set<String> sensitiveHeaders) {
        this.sensitiveHeaders = sensitiveHeaders;
    }

}
