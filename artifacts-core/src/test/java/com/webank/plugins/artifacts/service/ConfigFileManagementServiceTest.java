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

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.webank.plugins.artifacts.dto.FileQueryRequestDto;
import com.webank.plugins.artifacts.dto.FileQueryResultItemDto;
import com.webank.plugins.artifacts.dto.PackageComparisionRequestDto;
import com.webank.plugins.artifacts.dto.PackageComparisionResultDto;
import com.webank.plugins.artifacts.dto.SinglePackageQueryResultDto;
import com.webank.plugins.artifacts.interceptor.AuthorizationStorage;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQuery;
import com.webank.plugins.artifacts.support.cmdb.dto.v2.PaginationQueryResult;

@ActiveProfiles("test")
@RunWith(SpringRunner.class)
@SpringBootTest
public class ConfigFileManagementServiceTest {
    
    @Autowired
    ConfigFileManagementService service;
    
    ObjectMapper objectMapper = new ObjectMapper();
    
    @Before
    public void setUp() {
        String token = "***REMOVED***";
        token = String.format("Bearer %s", token);
        
        AuthorizationStorage.getIntance().set(token);
    }
    
    @Test
    public void testPackageComparision(){
        String unitDesignId = "0039_0000000017";
        String packageGuid = "0045_0000000005";
        
        String baselinePackageGuid = "0045_0000000005";
        
        PackageComparisionRequestDto comparisonReqDto = new PackageComparisionRequestDto();
        comparisonReqDto.setBaselinePackageId(baselinePackageGuid);
        
        PackageComparisionResultDto result =  service.packageComparision( unitDesignId,  packageGuid,
                 comparisonReqDto);
        
        System.out.println(toJson(result));
    }
    
    
    private String toJson(Object object){
        try {
            String sJson = objectMapper.writeValueAsString(object);
            return sJson;
        } catch (JsonProcessingException e) {
            throw new RuntimeException("", e);
        }
    }
    
    @Test
    public void testQuerySinglePackage() throws JsonProcessingException{
        String unitDesignId = "0039_0000000017";
        String packageId = "0045_0000000011";
//        String packageId = "0045_0000000005";
        SinglePackageQueryResultDto result = service.querySinglePackage( unitDesignId,  packageId);
        
        String sJson = objectMapper.writeValueAsString(result);
        System.out.println(sJson);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsConfDir() throws JsonProcessingException {
        String packageId = "0045_0000000005";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
        String filePath = "conf";
//        String filePath = "demo-app-spring-boot_1.5.3/conf/application-dev.properties";
        
        List<String> fileList = new ArrayList<String>();
        fileList.add(filePath);
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        
        String sJson = objectMapper.writeValueAsString(resultItemDtos);
        
        System.out.println(sJson);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsLeafFile() throws JsonProcessingException {
        String packageId = "0045_0000000005";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
        String filePath = "conf/application-dev.properties";
//        String filePath = "demo-app-spring-boot_1.5.3/conf/application-dev.properties";
        
        List<String> fileList = new ArrayList<String>();
        fileList.add(filePath);
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        
        String sJson = objectMapper.writeValueAsString(resultItemDtos);
        
        System.out.println(sJson);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsLeafFileWithBaseline() throws JsonProcessingException {
        String baselinePackageId = "0045_0000000005";
        String packageId = "0045_0000000011";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
        fileQueryRequestDto.setBaselinePackage(baselinePackageId);
        String filePath = "conf/application-dev.properties";
//        String filePath = "demo-app-spring-boot_1.5.3/conf/application-dev.properties";
        
        List<String> fileList = new ArrayList<String>();
        fileList.add(filePath);
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        
        String sJson = objectMapper.writeValueAsString(resultItemDtos);
        
        System.out.println(sJson);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsMultiFile() throws JsonProcessingException {
        String packageId = "0045_0000000005";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
        String filePath0 = "conf";
        String filePath1 = "bin";
//        String filePath = "demo-app-spring-boot_1.5.3/conf/application-dev.properties";
        
        List<String> fileList = new ArrayList<String>();
        fileList.add(filePath0);
        fileList.add(filePath1);
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        
        String sJson = objectMapper.writeValueAsString(resultItemDtos);
        
        System.out.println(sJson);
    }
    
    @Test
    public void testqueryDeployConfigFilesAsRootDir() throws JsonProcessingException {
        String packageId = "0045_0000000005";
        FileQueryRequestDto fileQueryRequestDto = new FileQueryRequestDto();
//        String filePath = "demo-app-spring-boot_1.5.3/conf/application-dev.properties";
        
        List<String> fileList = new ArrayList<String>();
        fileQueryRequestDto.setFileList(fileList);
        
        List<FileQueryResultItemDto> resultItemDtos = service.queryDeployConfigFiles(packageId, fileQueryRequestDto);
        
        
        String sJson = objectMapper.writeValueAsString(resultItemDtos);
        
        System.out.println(sJson);
    }

    @Test
    public void testQueryDeployPackages() {
        
        //pkg:0045_0000000005
        //http://124.156.108.126:19090/artifacts/unit-designs/0039_0000000017/packages/query
        String unitDesignId = "0039_0000000017";
        PaginationQuery query = new PaginationQuery();
        PaginationQueryResult<Map<String,Object>> result = service.queryDeployPackages(unitDesignId, query);
        
        System.out.println(result.getContents());
    }

}
