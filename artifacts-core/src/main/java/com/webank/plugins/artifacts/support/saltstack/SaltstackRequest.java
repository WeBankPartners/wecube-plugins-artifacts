package com.webank.plugins.artifacts.support.saltstack;

import java.util.List;
import java.util.Map;

public class SaltstackRequest<DATATYPE> {
    private List<DATATYPE> inputs;

    public SaltstackRequest<DATATYPE> withInputs(List<DATATYPE> inputs) {
        this.setInputs(inputs);
        return this;
    }

    public List<DATATYPE> getInputs() {
        return inputs;
    }

    public void setInputs(List<DATATYPE> inputs) {
        this.inputs = inputs;
    }

    public static class DefaultSaltstackRequest extends SaltstackRequest<Map<String, Object>> {
    }
}