package com.webank.plugins.artifacts.support.cmdb;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.webank.plugins.artifacts.commons.ApplicationProperties;

@Service
public class StandardCmdbEntityRestClient {

    @Autowired
    private CmdbRestTemplate template;

    @Autowired
    private ApplicationProperties applicationProperties;
    
    private static final String QUERY_DIFF_CONFIGURATION = "/wecmdb/entities/diff_configuration/query";
    
    public List<Map<String,Object>> queryDiffConfigurations(){
     return null;   
    }
}
