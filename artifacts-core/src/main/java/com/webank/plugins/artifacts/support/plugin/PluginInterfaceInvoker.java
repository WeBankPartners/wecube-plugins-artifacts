package com.webank.plugins.artifacts.support.plugin;

import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import com.webank.plugins.artifacts.domain.plugin.PluginConfigInterface;
import com.webank.plugins.artifacts.domain.plugin.PluginTriggerCommand;
import com.webank.plugins.artifacts.interceptor.UsernameStorage;
import com.webank.plugins.artifacts.support.plugin.dto.PluginResponse.ResultData;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@AllArgsConstructor
public class PluginInterfaceInvoker implements Runnable {

    @Data
    @AllArgsConstructor
    public static class InvocationResult {
        String operator;
        int rootCiTypeId;
        String serviceName;
        PluginConfigInterface inf;
        PluginTriggerCommand triggerCmd;
        List<Map<String, Object>> pluginParameters;
        List<Object> pluginResponse;
    }

    private String instanceAddress;
    private String operator;
    private int rootCiTypeId;
    private String serviceName;
    private String interfacePath;
    private PluginConfigInterface inf;
    private PluginTriggerCommand triggerCmd;

    private List<Map<String, Object>> pluginParameters;
    private PluginServiceStub pluginServiceStub;

    private Consumer<InvocationResult> callback;

    @Override
    public void run() {
        UsernameStorage.getIntance().set(operator);
        List<Object> result = null;
        try {
            result = invokePluginInterface();
        } catch (Exception exception) {
            log.error("Plugin remote call failure - " + exception.getMessage(), exception);
        }
        if (callback!=null) callback.accept(new InvocationResult(operator,rootCiTypeId, serviceName, inf, triggerCmd, pluginParameters, result));
    }

    private List<Object> invokePluginInterface() {
        ResultData<Object> responseData = pluginServiceStub.callPluginInterface(instanceAddress, interfacePath, pluginParameters);
        return responseData == null ? null : responseData.getOutputs();
    }

}
