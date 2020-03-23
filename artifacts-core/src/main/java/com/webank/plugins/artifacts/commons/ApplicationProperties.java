package com.webank.plugins.artifacts.commons;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import lombok.Data;

@Data
@Component
@ConfigurationProperties(prefix = "plugins")
public class ApplicationProperties {

    private String wecubePlatformServerUrl = "";
    private String wecubePlatformToken = "";
    private String wecmdbServerUrl = "";
    private String saltstackServerUrl = "";
    private String artifactsS3ServerUrl = "";
    private String artifactsS3AccessKey = "";
    private String artifactsS3SecretKey = "";
    private Map<String, String> customHeaders = new LinkedHashMap<>();
    private Set<String> sensitiveHeaders = null;

    @Data
    @ConfigurationProperties(prefix = "plugins")
    public class CmdbDataProperties {
        private Integer enumCategoryTypeSystem = 1;
        private Integer ciTypeIdOfSystemDesign = 37;
        private Integer ciTypeIdOfUnitDesign = 39;
        private Integer ciTypeIdOfPackage = 45;
        private String enumCategoryNameOfDiffConf = "diff_conf";
        private String propertyNameOfFixedDate = "fixed_date";
        private String enumCodeChangeOfCiStateOfCreate = "update";
        private String enumCodeDestroyedOfCiStateOfCreate = "delete";
    }
}
