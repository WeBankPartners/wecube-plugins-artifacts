package com.webank.plugins.artifacts.controller;

import static org.springframework.web.bind.annotation.RequestMethod.DELETE;
import static org.springframework.web.bind.annotation.RequestMethod.GET;
import static org.springframework.web.bind.annotation.RequestMethod.HEAD;
import static org.springframework.web.bind.annotation.RequestMethod.OPTIONS;
import static org.springframework.web.bind.annotation.RequestMethod.PATCH;
import static org.springframework.web.bind.annotation.RequestMethod.POST;
import static org.springframework.web.bind.annotation.RequestMethod.PUT;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import com.webank.plugins.artifacts.commons.ApplicationProperties;
import com.webank.plugins.artifacts.service.helper.ProxyExchange;

@RestController
public class WecubePlatformApiProxyController {

    private static final Logger log = LoggerFactory.getLogger(WecubePlatformApiProxyController.class);

    private static final String API_PROXY_PATH = "/platform";

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private ApplicationProperties applicationProperties;

    @RequestMapping(value = API_PROXY_PATH + "/**", method = { GET, DELETE, OPTIONS, HEAD })
    public void pluginApiProxy(HttpServletRequest request, HttpServletResponse response) {
        proxy(createProxyExchange(request, response), request);
    }

    @RequestMapping(value = API_PROXY_PATH + "/**", method = { POST, PUT, PATCH })
    public void pluginApiProxy(HttpServletRequest request, HttpServletResponse response, @RequestBody Object body) {
        proxy(createProxyExchange(request, response).body(body), request);
    }

    private ProxyExchange createProxyExchange(HttpServletRequest request, HttpServletResponse response) {
        ProxyExchange proxyExchange = new ProxyExchange(restTemplate, request, response);
        proxyExchange.customHttpHeaders(applicationProperties.getCustomHeaders());
        proxyExchange.sensitiveHeaders(applicationProperties.getSensitiveHeaders());
        return proxyExchange;
    }

    private void proxy(ProxyExchange proxyExchange, HttpServletRequest request) {
        log.info("http {} request comes: {}", request.getMethod(), proxyExchange.path());
        routing(proxyExchange, request);

        proxyExchange.exchange();
    }

    private void routing(ProxyExchange proxyExchange, HttpServletRequest request) {
        String targetUri = deriveTargetUrl(request.getScheme(), proxyExchange.path(API_PROXY_PATH));

        log.info("routing to : " + targetUri);

        proxyExchange.targetUri(targetUri);
    }

    private String deriveTargetUrl(String scheme, String path) {
        return applicationProperties.getWecubeGatewayServerUrl() + path;
    }

}