package com.webank.plugins.artifacts.commons;

public class PluginException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public PluginException(String message) {
        super(message);
    }

    public PluginException(String message, Throwable cause) {
        super(message, cause);
    }
}
