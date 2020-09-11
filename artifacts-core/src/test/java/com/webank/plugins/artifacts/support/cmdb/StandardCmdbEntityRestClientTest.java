package com.webank.plugins.artifacts.support.cmdb;

import static org.junit.Assert.*;

import java.util.List;
import java.util.Map;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit4.SpringRunner;

import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;

@ActiveProfiles("test")
@RunWith(SpringRunner.class)
@SpringBootTest
public class StandardCmdbEntityRestClientTest {
    
    @Autowired
    private StandardCmdbEntityRestClient client;
    
    @Before
    public void setUp() {
        String token = "***REMOVED***";
        token = String.format("Bearer %s", token);
        
        AuthorizationStorage.getIntance().set(token);
    }

    @Test
    public void testQueryDiffConfigurations() {
        List<Map<String,Object>> results = client.queryDiffConfigurations();
        for(Map<String,Object> result : results) {
            System.out.println("==========================");
            result.entrySet().forEach(e -> {
                System.out.println(String.format("k:%s, v:%s", e.getKey(), e.getValue()));
            } );
        }
    }

}
