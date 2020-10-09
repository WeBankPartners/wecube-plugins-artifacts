package com.webank.plugins.artifacts.support.cmdb;

import static org.junit.Assert.fail;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest
public class CmdbServiceV2StubTest {
    
    @Autowired
    protected CmdbServiceV2Stub cmdbServiceV2Stub;

    @Test
    public void testCreateCiData() {
        fail("Not yet implemented");
    }

}
