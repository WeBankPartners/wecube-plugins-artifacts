package com.webank.plugins.artifacts.support.saltstack;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

@Data
public class SaltstackResponse<DATATYPE> {
    public static final String RESULT_CODE_OK = "0";

    private String resultCode;
    private String resultMessage;
    @JsonProperty("results")
    private ResultData<DATATYPE> resultData;

    public List<DATATYPE> getOutputs() {
        return (getResultData() == null) ? null : getResultData().getOutputs();
    }

    public ResultData<DATATYPE> getResultData() {
        return resultData;
    }

    public void setResultData(ResultData<DATATYPE> resultData) {
        this.resultData = resultData;
    }

    public String getResultCode() {
        return resultCode;
    }

    public void setResultCode(String resultCode) {
        this.resultCode = resultCode;
    }

    public String getResultMessage() {
        return resultMessage;
    }

    public void setResultMessage(String resultMessage) {
        this.resultMessage = resultMessage;
    }

    public static class ResultData<DATATYPE> {
        private List<DATATYPE> outputs;

        public List<DATATYPE> getOutputs() {
            return outputs;
        }

        public void setOutputs(List<DATATYPE> outputs) {
            this.outputs = outputs;
        }
    }

    public static class DefaultSaltstackResponse extends SaltstackResponse<Object> {
    }

    @Override
    public String toString() {
        return "SaltstackResponse [resultCode=" + resultCode + ", resultMessage=" + resultMessage + ", resultData=" + resultData + "]";
    }
}
