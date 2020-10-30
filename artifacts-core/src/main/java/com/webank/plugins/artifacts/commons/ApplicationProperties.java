package com.webank.plugins.artifacts.commons;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "plugins")
public class ApplicationProperties {

    private String wecubeGatewayServerUrl = "";
    private String artifactsS3ServerUrl = "";
    private String artifactsS3AccessKey = "";
    private String artifactsS3SecretKey = "";
    private String artifactsS3BucketName = "";
    private String artifactsNexusServerUrl = "";
    private String artifactsNexusUsername = "";
    private String artifactsNexusPassword = "";
    private String artifactsNexusRepository = "";
    private String cmdbArtifactPath = "";
    private Map<String, String> customHeaders = new LinkedHashMap<>();
    private Set<String> sensitiveHeaders = null;
    private String jwtSigningKey = "Platform+Auth+Server+Secret";
    private boolean artifactsLocalEnabled = true;
    private boolean artifactsNexusEnabled = true;
    private String propertyEncryptKeyPath;
    
    public String getPropertyEncryptKeyPath() {
        return propertyEncryptKeyPath;
    }

    public void setPropertyEncryptKeyPath(String propertyEncryptKeyPath) {
        this.propertyEncryptKeyPath = propertyEncryptKeyPath;
    }

    public String getWecubeGatewayServerUrl() {
        return wecubeGatewayServerUrl;
    }

    public void setWecubeGatewayServerUrl(String wecubeGatewayServerUrl) {
        this.wecubeGatewayServerUrl = wecubeGatewayServerUrl;
    }

    public String getArtifactsS3ServerUrl() {
        return artifactsS3ServerUrl;
    }

    public void setArtifactsS3ServerUrl(String artifactsS3ServerUrl) {
        this.artifactsS3ServerUrl = artifactsS3ServerUrl;
    }

    public String getArtifactsS3AccessKey() {
        return artifactsS3AccessKey;
    }

    public void setArtifactsS3AccessKey(String artifactsS3AccessKey) {
        this.artifactsS3AccessKey = artifactsS3AccessKey;
    }

    public String getArtifactsS3SecretKey() {
        return artifactsS3SecretKey;
    }

    public void setArtifactsS3SecretKey(String artifactsS3SecretKey) {
        this.artifactsS3SecretKey = artifactsS3SecretKey;
    }

    public String getArtifactsS3BucketName() {
        return artifactsS3BucketName;
    }

    public void setArtifactsS3BucketName(String artifactsS3BucketName) {
        this.artifactsS3BucketName = artifactsS3BucketName;
    }

    public String getArtifactsNexusServerUrl() {
        return artifactsNexusServerUrl;
    }

    public void setArtifactsNexusServerUrl(String artifactsNexusServerUrl) {
        this.artifactsNexusServerUrl = artifactsNexusServerUrl;
    }

    public String getArtifactsNexusUsername() {
        return artifactsNexusUsername;
    }

    public void setArtifactsNexusUsername(String artifactsNexusUsername) {
        this.artifactsNexusUsername = artifactsNexusUsername;
    }

    public String getArtifactsNexusPassword() {
        return artifactsNexusPassword;
    }

    public void setArtifactsNexusPassword(String artifactsNexusPassword) {
        this.artifactsNexusPassword = artifactsNexusPassword;
    }

    public String getArtifactsNexusRepository() {
        return artifactsNexusRepository;
    }

    public void setArtifactsNexusRepository(String artifactsNexusRepository) {
        this.artifactsNexusRepository = artifactsNexusRepository;
    }

    public String getCmdbArtifactPath() {
        return cmdbArtifactPath;
    }

    public void setCmdbArtifactPath(String cmdbArtifactPath) {
        this.cmdbArtifactPath = cmdbArtifactPath;
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

    public String getJwtSigningKey() {
        return jwtSigningKey;
    }

    public void setJwtSigningKey(String jwtSigningKey) {
        this.jwtSigningKey = jwtSigningKey;
    }

    public boolean isArtifactsLocalEnabled() {
        return artifactsLocalEnabled;
    }

    public void setArtifactsLocalEnabled(boolean artifactsLocalEnabled) {
        this.artifactsLocalEnabled = artifactsLocalEnabled;
    }

    public boolean isArtifactsNexusEnabled() {
        return artifactsNexusEnabled;
    }

    public void setArtifactsNexusEnabled(boolean artifactsNexusEnabled) {
        this.artifactsNexusEnabled = artifactsNexusEnabled;
    }

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

        public Integer getEnumCategoryTypeSystem() {
            return enumCategoryTypeSystem;
        }

        public void setEnumCategoryTypeSystem(Integer enumCategoryTypeSystem) {
            this.enumCategoryTypeSystem = enumCategoryTypeSystem;
        }

        public Integer getCiTypeIdOfSystemDesign() {
            return ciTypeIdOfSystemDesign;
        }

        public void setCiTypeIdOfSystemDesign(Integer ciTypeIdOfSystemDesign) {
            this.ciTypeIdOfSystemDesign = ciTypeIdOfSystemDesign;
        }

        public Integer getCiTypeIdOfUnitDesign() {
            return ciTypeIdOfUnitDesign;
        }

        public void setCiTypeIdOfUnitDesign(Integer ciTypeIdOfUnitDesign) {
            this.ciTypeIdOfUnitDesign = ciTypeIdOfUnitDesign;
        }

        public Integer getCiTypeIdOfPackage() {
            return ciTypeIdOfPackage;
        }

        public void setCiTypeIdOfPackage(Integer ciTypeIdOfPackage) {
            this.ciTypeIdOfPackage = ciTypeIdOfPackage;
        }

        public String getEnumCategoryNameOfDiffConf() {
            return enumCategoryNameOfDiffConf;
        }

        public void setEnumCategoryNameOfDiffConf(String enumCategoryNameOfDiffConf) {
            this.enumCategoryNameOfDiffConf = enumCategoryNameOfDiffConf;
        }

        public String getPropertyNameOfFixedDate() {
            return propertyNameOfFixedDate;
        }

        public void setPropertyNameOfFixedDate(String propertyNameOfFixedDate) {
            this.propertyNameOfFixedDate = propertyNameOfFixedDate;
        }

        public String getEnumCodeChangeOfCiStateOfCreate() {
            return enumCodeChangeOfCiStateOfCreate;
        }

        public void setEnumCodeChangeOfCiStateOfCreate(String enumCodeChangeOfCiStateOfCreate) {
            this.enumCodeChangeOfCiStateOfCreate = enumCodeChangeOfCiStateOfCreate;
        }

        public String getEnumCodeDestroyedOfCiStateOfCreate() {
            return enumCodeDestroyedOfCiStateOfCreate;
        }

        public void setEnumCodeDestroyedOfCiStateOfCreate(String enumCodeDestroyedOfCiStateOfCreate) {
            this.enumCodeDestroyedOfCiStateOfCreate = enumCodeDestroyedOfCiStateOfCreate;
        }

    }
}
