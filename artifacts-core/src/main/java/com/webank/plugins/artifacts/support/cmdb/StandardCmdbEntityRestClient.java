package com.webank.plugins.artifacts.support.cmdb;

import java.net.URI;
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
import com.webank.plugins.artifacts.support.cmdb.dto.EntityQuerySpecification;
import com.webank.plugins.artifacts.support.cmdb.dto.StandardCmdbEntityResponseDto;

@Service
public class StandardCmdbEntityRestClient {
    private static final Logger log = LoggerFactory.getLogger(StandardCmdbEntityRestClient.class);
    private static final String QUERY_DIFF_CONFIGURATION = "/wecmdb/entities/diff_configuration/query";

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private ApplicationProperties applicationProperties;

    private ObjectMapper objectMapper = new ObjectMapper();

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
