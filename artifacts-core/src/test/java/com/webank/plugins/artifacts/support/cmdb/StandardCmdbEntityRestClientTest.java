package com.webank.plugins.artifacts.support.cmdb;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit4.SpringRunner;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbDiffConfigDto;

@ActiveProfiles("test")
@RunWith(SpringRunner.class)
@SpringBootTest
public class StandardCmdbEntityRestClientTest {

    @Autowired
    private StandardCmdbEntityRestClient client;
    
    ObjectMapper objectMapper = new ObjectMapper();

    @Before
    public void setUp() {
        String token = "***REMOVED***";
        token = String.format("Bearer %s", token);

        AuthorizationStorage.getIntance().set(token);
    }
    
    @Test
    public void testCreateDiffConfigurationCi(){
        String varName = "gl_diff_key_3";
        String varValue = null;
        CmdbDiffConfigDto result = client.createDiffConfigurationCi( varName,  varValue);
        System.out.println(toJson(result));
    }
    
    

    @Test
    public void testCreateEntity() {
        String entityName = "diff_configuration";
        List<Map<String, Object>> requestParams = new ArrayList<>();
        Map<String, Object> requestDataMap = new HashMap<>();
        requestDataMap.put("code", "gl_diff_key");
        requestDataMap.put("variable_name", "gl_diff_key");
        requestDataMap.put("variable_value", "ddd");

        requestParams.add(requestDataMap);
        Object result = client.createEntity(entityName, requestParams);
        System.out.println(toJson(result));
    }

    @Test
    public void testQueryDiffConfigurations() {
        List<Map<String, Object>> results = client.queryDiffConfigurations();
        for (Map<String, Object> result : results) {
            System.out.println("==========================");
            result.entrySet().forEach(e -> {
                System.out.println(String.format("k:%s, v:%s", e.getKey(), e.getValue()));
            });
        }
    }
    
    private String toJson(Object object){
        try {
            String sJson = objectMapper.writeValueAsString(object);
            return sJson;
        } catch (JsonProcessingException e) {
            throw new RuntimeException("", e);
        }
    }

}
