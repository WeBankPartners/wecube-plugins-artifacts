package com.webank.plugins.artifacts.support.saltstack;

import com.webank.plugins.artifacts.support.RemoteCallException;

public class SaltstackRemoteCallException extends RemoteCallException {

    private transient SaltstackResponse SaltstackResponse;

    public SaltstackRemoteCallException(String message) {
        super(message);
    }

    public SaltstackRemoteCallException(String message, SaltstackResponse SaltstackResponse) {
        super(message);
        this.SaltstackResponse = SaltstackResponse;
    }

    public SaltstackRemoteCallException(String message, SaltstackResponse SaltstackResponse, Throwable cause) {
        super(message, cause);
        this.SaltstackResponse = SaltstackResponse;
    }

    public SaltstackResponse getSaltstackResponse() {
        return SaltstackResponse;
    }

    @Override
    public String getErrorMessage() {
        return String.format("%s (Call Saltstack meet error: %s)", this.getMessage(), getStatusCode(SaltstackResponse));
    }

    @Override
    public Object getErrorData() {
        return SaltstackResponse == null ? null : SaltstackResponse.getResultData();
    }

    private String getStatusCode(SaltstackResponse SaltstackResponse) {
        return SaltstackResponse == null ? null : SaltstackResponse.getResultCode();
    }
}
