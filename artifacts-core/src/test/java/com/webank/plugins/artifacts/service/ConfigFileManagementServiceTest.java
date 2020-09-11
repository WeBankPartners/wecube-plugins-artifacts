package com.webank.plugins.artifacts.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit4.SpringRunner;

import com.webank.plugins.artifacts.dto.FileQueryRequestDto;
import com.webank.plugins.artifacts.dto.FileQueryResultItemDto;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;

@ActiveProfiles("test")
@RunWith(SpringRunner.class)
@SpringBootTest
public class ConfigFileManagementServiceTest {
    
    @Autowired
    ConfigFileManagementService service;
    
    @Before
    public void setUp() {
        String token = "***REMOVED***";
        token = String.format("Bearer %s", token);
        
        AuthorizationStorage.getIntance().set(token);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsRootDir() {
        String packageId = "0045_0000000005";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
//        String filePath = "demo-app-spring-boot_1.5.3";
        
        List<String> fileList = new ArrayList<String>();
//        fileList.add(filePath);
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        System.out.println(resultItemDtos.size());
        System.out.println(resultItemDtos);
    }

    @Test
    public void testQueryDeployPackages() {
        
        //pkg:0045_0000000005
        //http://124.156.108.126:19090/artifacts/unit-designs/0039_0000000017/packages/query
        String unitDesignId = "0039_0000000017";
        PaginationQuery query = new PaginationQuery();
        PaginationQueryResult<Map<String,Object>> result = service.queryDeployPackages(unitDesignId, query);
        
        System.out.println(result.getContents().size());
    }

}
