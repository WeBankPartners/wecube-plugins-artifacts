package com.webank.plugins.artifacts.support.nexus;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

import org.springframework.web.client.RestTemplate;

import static org.springframework.http.HttpMethod.GET;

@Component
@Slf4j
public class NexusClient {

    @Autowired
    private RestTemplate restTemplate;

    @SuppressWarnings("unchecked")
    public <D, R extends NexusResponse> D  get(String targetUrl, String nexusUsername, String nexusPassword, Class<R> responseType) {
        log.info("About to call {} ", targetUrl);
        HttpHeaders headers = new HttpHeaders();
        headers.setBasicAuth(nexusUsername,nexusPassword);
        ResponseEntity<R> rResponseEntity = restTemplate.exchange(targetUrl, GET, new HttpEntity<>(headers), responseType);
        log.info("Nexus response: {} ", rResponseEntity);
        return  (D)rResponseEntity.getBody().getItems();
    }
}
