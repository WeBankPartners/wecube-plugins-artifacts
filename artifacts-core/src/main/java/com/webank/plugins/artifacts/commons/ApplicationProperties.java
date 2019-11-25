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
        private Integer enumCategoryTypeCommon = 2;
        private Integer ciTypeIdOfIdcDesign = 22;
        private Integer ciTypeIdOfIdc = 16;
        private Integer ciTypeIdOfSystemDesign = 1;
        private Integer ciTypeIdOfSubsys = 7;
        private Integer ciTypeIdOfUnitDesign = 3;
        private Integer ciTypeIdOfPackage = 11;
        private String referenceNameOfRelate = "鍏宠仈";
        private String referenceNameOfBelong = "灞炰簬";
        private String referenceNameOfRealize = "瀹炵幇";
        private Integer ciTypeIdOfZoneLinkDesign = 24;
        private Integer ciTypeIdOfZone = 17;
        private Integer ciTypeIdOfZoneLink = 18;
        private Integer ciTypeIdOfZoneDesign = 23;

        //for getApplicationDeploymentDesignDataTreeBySystemDesignGuidAndEnvCode()
        private Integer ciTypeIdOfHost = 12;
        private Integer ciTypeIdOfInstance = 15;
        private Integer ciTypeIdOfUnit = 8;
        private Integer ciTypeIdOfSubsystemDesign = 2;
        private String referenceNameOfRunning = "杩愯鍦�";

        private String enumCategoryCiTypeLayer = "ci_layer";
        private String enumCategoryCiTypeCatalog = "ci_catalog";
        private String enumCategoryCiTypeZoomLevels = "ci_zoom_level";
        private String enumCategoryNameOfEnv = "env";
        private String enumCategoryNameOfDiffConf = "diff_conf";
        private String enumCodeOfStateDelete = "delete";
        private String propertyNameOfFixedDate = "fixed_date";
        private String enumCategoryCiStateOfCreate = "ci_state_create";
        private String enumCodeChangeOfCiStateOfCreate = "update";
        private String enumCodeDestroyedOfCiStateOfCreate = "delete";


        private String statusAttributeName = "status";
        private String businessKeyAttributeName = "bizKey";
        private String catNameOfDeployDesign = "tab_of_deploy_design";
        private String catNameOfArchitectureDesign = "tab_of_architecture_design";
        private String catNameOfPlanningDesign = "tab_of_planning_design";
        private String catNameOfResourcePlanning = "tab_of_resource_planning";
        private String catNameOfQueryDeployDesign = "tab_query_of_deploy_design";
        private String codeOfDeployDetail = "guid_of_deploy_detail";
        private String propertyNameOfState = "state";
    }

    @Data
    @ConfigurationProperties(prefix = "plugins")
    public class PluginProperties {
        private String pluginDeployPath;
        private String[] pluginHosts;
        private String pluginPackageBucketName;
        private String registerFile;
        private String pluginPackageNameOfDeploy;
        private String defaultHostSshUser;
        private String defaultHostSshPassword;
        private Integer defaultHostSshPort;
    }

}
