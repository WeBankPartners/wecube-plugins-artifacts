package com.webank.plugins.artifacts.support.nexus;

import com.webank.plugins.artifacts.support.cmdb.dto.CmdbResponse;
import com.webank.plugins.artifacts.support.nexus.NexusResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@Component
@Slf4j
public class NexusClient {

    @Autowired
    private RestTemplate restTemplate;

    @SuppressWarnings("unchecked")
    public <D, R extends NexusResponse> D  get(String targetUrl, Class<R> responseType) {
        log.info("About to call {} ", targetUrl);
        R NexusResponse = restTemplate.getForObject(targetUrl, responseType);
        log.info("Nexus response: {} ", NexusResponse);
        return  (D)NexusResponse.getItems();
    }
}
