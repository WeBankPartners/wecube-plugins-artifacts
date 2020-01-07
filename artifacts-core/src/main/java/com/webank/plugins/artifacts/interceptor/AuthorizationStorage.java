package com.webank.plugins.artifacts.interceptor;

public class AuthorizationStorage extends ThreadLocal<String> {
    private static AuthorizationStorage instance = new AuthorizationStorage();

    public static AuthorizationStorage getIntance() {
        return instance;
    }
}