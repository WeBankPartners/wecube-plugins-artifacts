package com.webank.plugins.artifacts.support.nexus;

import static org.springframework.http.HttpMethod.GET;

import java.net.URI;
import java.util.Arrays;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class NexusClient {
    private static final Logger log = LoggerFactory.getLogger(NexusClient.class);

    @Autowired
    private RestTemplate restTemplate;
    

    @SuppressWarnings("unchecked")
    public NexusSearchAssetResponse  searchAsset(URI targetUri, String nexusUsername, String nexusPassword) {
        log.info("About to call {} ", targetUri.toString());
        HttpHeaders headers = new HttpHeaders();
        headers.setBasicAuth(nexusUsername,nexusPassword);
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(Arrays.asList(MediaType.APPLICATION_JSON));
        
        ResponseEntity<NexusSearchAssetResponse> responseEntity  = restTemplate.exchange(targetUri, GET, new HttpEntity<>(headers), NexusSearchAssetResponse.class);
        return  responseEntity.getBody();
    }

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
