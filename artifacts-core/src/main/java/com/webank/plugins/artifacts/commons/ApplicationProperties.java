package com.webank.plugins.artifacts.commons;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import lombok.Data;

@Data
@Component
@ConfigurationProperties(prefix = "plugins")
public class ApplicationProperties {

    private String wecmdbServerUrl = "";
    private String saltstackServerUrl = "";
    private String artifactsS3ServerUrl = "";
    private String artifactsS3AccessKey = "";
    private String artifactsS3SecretKey = "";
    
    @Data
    @ConfigurationProperties(prefix = "plugins")
    public class CmdbDataProperties {
        private Integer enumCategoryTypeSystem = 1;
        private Integer ciTypeIdOfSystemDesign = 1;
        private Integer ciTypeIdOfUnitDesign = 3;
        private Integer ciTypeIdOfPackage = 12;
        private String enumCategoryNameOfDiffConf = "diff_conf";
        private String propertyNameOfFixedDate = "fixed_date";
        private String enumCodeChangeOfCiStateOfCreate = "update";
        private String enumCodeDestroyedOfCiStateOfCreate = "delete";
    }
}
