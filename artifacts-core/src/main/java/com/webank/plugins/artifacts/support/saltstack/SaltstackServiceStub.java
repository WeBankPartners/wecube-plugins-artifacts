package com.webank.plugins.artifacts.support.saltstack;

import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.DefaultSaltstackResponse;
import com.webank.plugins.artifacts.support.saltstack.SaltstackResponse.ResultData;

import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j
public class SaltstackServiceStub {
    @Autowired
    RestTemplate restTemplate;

    private static final String pluginContextPath = "/saltstack";
    private static final String INF_RELEASED_PACKAGE_LIST_DIR = "/v1/released-package/listCurrentDir";
    private static final String INF_RELEASED_PACKAGE_PROPERTY_KEY = "/v1/released-package/getConfigFileKey";

    public ResultData<Object> getReleasedPackageFilesByCurrentDir(String wecubeGatewayUrl,
            SaltstackRequest<Map<String, Object>> request) {
        return post(asServerUrl(wecubeGatewayUrl, INF_RELEASED_PACKAGE_LIST_DIR), request);
    }

    public ResultData<Object> getReleasedPackagePropertyKeysByFilePath(String saltstackServerUrl,
            SaltstackRequest<Map<String, Object>> request) {
        return post(asServerUrl(saltstackServerUrl, INF_RELEASED_PACKAGE_PROPERTY_KEY), request);
    }

    private ResultData<Object> post(String targetUrl, SaltstackRequest parameters) {
        log.info("About to call {} with parameters: {} ", targetUrl, parameters);
        SaltstackResponse<Object> response = restTemplate.postForObject(targetUrl, parameters, DefaultSaltstackResponse.class);
        log.info("Saltstack plugin response: {} ", response);
        validateResponse(response, false);

        return response.getResultData();
    }

    private void validateResponse(SaltstackResponse response, boolean dataRequired) {
        if (response == null) {
            throw new SaltstackRemoteCallException("Saltstack plugin failure due to no response.");
        }
        if (!SaltstackResponse.RESULT_CODE_OK.equalsIgnoreCase(response.getResultCode())) {
            throw new SaltstackRemoteCallException("Saltstack plugin call error: " + response.getResultMessage(), response);
        }
        if (dataRequired && response.getOutputs() == null) {
            throw new SaltstackRemoteCallException("Saltstack plugin call failure due to unexpected empty response.", response);
        }
    }

    private String asServerUrl(String serverUrl, String originPath, Object... pathVariables) {
        String solvedPath = originPath;
        if (pathVariables != null && pathVariables.length > 0) {
            solvedPath = String.format(originPath, pathVariables);
        }
        return serverUrl + "/" + pluginContextPath + solvedPath;
    }
}
