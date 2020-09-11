package com.webank.plugins.artifacts.support.cmdb;

import java.net.URI;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.support.cmdb.dto.CmdbDiffConfigDto;
import com.webank.plugins.artifacts.support.cmdb.dto.EntityQuerySpecification;
import com.webank.plugins.artifacts.support.cmdb.dto.StandardCmdbEntityResponseDto;

@Service
public class StandardCmdbEntityRestClient {
    private static final Logger log = LoggerFactory.getLogger(StandardCmdbEntityRestClient.class);
    private static final String QUERY_DIFF_CONFIGURATION = "/wecmdb/entities/diff_configuration/query";
    private static final String CREATE_REQUEST_URL = "/wecmdb/entities/{entity-name}/create";

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private ApplicationProperties applicationProperties;

    private ObjectMapper objectMapper = new ObjectMapper();

    @SuppressWarnings("unchecked")
    public CmdbDiffConfigDto createDiffConfigurationCi(String varName, String varValue) {
        String entityName = "diff_configuration";
        List<Map<String, Object>> requestParams = new ArrayList<>();
        Map<String, Object> requestDataMap = new HashMap<>();
        requestDataMap.put("code", varName);
        requestDataMap.put("variable_name", varName);
        requestDataMap.put("variable_value", varValue);

        requestParams.add(requestDataMap);
        Object result = createEntity(entityName, requestParams);
        if(result == null){
            return null;
        }
        if (result instanceof List) {
            List<Object> resultList = (List<Object>) result;
            if (resultList.size() > 0) {
                Map<String, Object> diffConfigMap = (Map<String, Object>) resultList.get(0);
                CmdbDiffConfigDto dto = new CmdbDiffConfigDto();
                dto.setDiffExpr((String) diffConfigMap.get("variable_value"));
                dto.setGuid((String) diffConfigMap.get("guid"));
                dto.setKey((String) diffConfigMap.get("code"));
                dto.setDisplayName((String) diffConfigMap.get("displayName"));
                return dto;
            }

        }else if(result instanceof Map){
            Map<String, Object> diffConfigMap = (Map<String, Object>) result;
            CmdbDiffConfigDto dto = new CmdbDiffConfigDto();
            dto.setDiffExpr((String) diffConfigMap.get("variable_value"));
            dto.setGuid((String) diffConfigMap.get("guid"));
            dto.setKey((String) diffConfigMap.get("code"));
            dto.setDisplayName((String) diffConfigMap.get("displayName"));
            return dto;
        }

        return null;
    }

    public Object createEntity(String entityName, List<Map<String, Object>> requestParams) {
        String requestUriStr = String.format("%s%s", applicationProperties.getWecubeGatewayServerUrl(),
                CREATE_REQUEST_URL);
        URI requestUri = restTemplate.getUriTemplateHandler().expand(requestUriStr, entityName);

        long timeMilliSeconds = System.currentTimeMillis();
        if (log.isInfoEnabled()) {
            log.info("SEND QUERY post [{}] url={}, request={}", timeMilliSeconds, requestUri.toString(),
                    toJson(requestParams));
        }
        StandardCmdbEntityResponseDto result = restTemplate.postForObject(requestUri, requestParams,
                StandardCmdbEntityResponseDto.class);

        if (log.isInfoEnabled()) {
            log.info("RECEIVE QUERY post [{}] url={},result={}", timeMilliSeconds, requestUri.toString(), result);
        }

        if (StandardCmdbEntityResponseDto.STATUS_ERROR.equals(result.getStatus())) {
            throw new PluginException(result.getMessage());
        }

        return result.getData();
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> queryDiffConfigurations() {
        EntityQuerySpecification spec = new EntityQuerySpecification();
        StandardCmdbEntityResponseDto respDto = query(spec);
        log.info("data:{}", respDto.getData());
        return (List<Map<String, Object>>) respDto.getData();
    }

    protected StandardCmdbEntityResponseDto query(EntityQuerySpecification querySpec) {
        String requestUriStr = String.format("%s%s", applicationProperties.getWecubeGatewayServerUrl(),
                QUERY_DIFF_CONFIGURATION);
        URI requestUri = restTemplate.getUriTemplateHandler().expand(requestUriStr);

        long timeMilliSeconds = System.currentTimeMillis();
        if (log.isInfoEnabled()) {
            log.info("SEND QUERY post [{}] url={}, request={}", timeMilliSeconds, requestUri.toString(),
                    toJson(querySpec));
        }
        StandardCmdbEntityResponseDto result = restTemplate.postForObject(requestUri, querySpec,
                StandardCmdbEntityResponseDto.class);
        if (log.isDebugEnabled()) {
            log.debug("RECEIVE QUERY post [{}] url={},result={}", timeMilliSeconds, requestUri.toString(), result);
        }
        return result;
    }

    private String toJson(Object value) {
        try {
            String json = objectMapper.writeValueAsString(value);
            return json;
        } catch (JsonProcessingException e) {
            log.info("errors to convert json object", e);
            return "";
        }
    }
}
