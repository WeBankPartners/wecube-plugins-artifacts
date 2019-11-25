package com.webank.plugins.artifacts.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

import com.webank.plugins.artifacts.commons.ApplicationProperties.CmdbDataProperties;
import com.webank.plugins.artifacts.commons.ApplicationProperties.PluginProperties;

@Configuration
@EnableConfigurationProperties({PluginProperties.class, CmdbDataProperties.class})
@ComponentScan({ "com.webank.plugins.artifacts" })
public class SpringAppConfig {

}
