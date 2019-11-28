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

    private static final String INF_RELEASED_PACKAGE_LIST_DIR = "/saltstack/v1/released-package/listCurrentDir";
    private static final String INF_RELEASED_PACKAGE_PROPERTY_KEY = "/saltstack/v1/released-package/getConfigFileKey";

    public ResultData<Object> getReleasedPackageFilesByCurrentDir(String saltstackServerUrl,
            SaltstackRequest<Map<String, Object>> request) {
        return callSaltstackInterface(asSaltstackServerUrl(saltstackServerUrl, INF_RELEASED_PACKAGE_LIST_DIR), request);
    }
    
    public ResultData<Object> getReleasedPackagePropertyKeysByFilePath(String instanceAddress,
            SaltstackRequest<Map<String, Object>> request) {
        return callSaltstackInterface(asSaltstackServerUrl(instanceAddress, INF_RELEASED_PACKAGE_PROPERTY_KEY), request);
    }
    
    private ResultData<Object> callSaltstackInterface(String targetUrl, SaltstackRequest parameters) {
        log.info("About to call {} with parameters: {} ", targetUrl, parameters);
        SaltstackResponse<Object> response = restTemplate.postForObject(targetUrl, parameters, DefaultSaltstackResponse.class);
        log.info("Plugin response: {} ", response);
        validateSaltstackResponse(response, false);

        return response.getResultData();
    }

    private void validateSaltstackResponse(SaltstackResponse SaltstackResponse, boolean dataRequired) {
        if (SaltstackResponse == null) {
            throw new SaltstackRemoteCallException("Plugin call failure due to no response.");
        }
        if (!SaltstackResponse.RESULT_CODE_OK.equalsIgnoreCase(SaltstackResponse.getResultCode())) {
            throw new SaltstackRemoteCallException("Plugin call error: " + SaltstackResponse.getResultMessage(), SaltstackResponse);
        }
        if (dataRequired && SaltstackResponse.getOutputs() == null) {
            throw new SaltstackRemoteCallException("Plugin call failure due to unexpected empty response.", SaltstackResponse);
        }
    }

    private String asSaltstackServerUrl(String saltstackServerUrl, String originPath, Object... pathVariables) {
        String solvedPath = originPath;
        if (pathVariables != null && pathVariables.length > 0) {
            solvedPath = String.format(originPath, pathVariables);
        }
        return saltstackServerUrl + solvedPath;
    }
}
