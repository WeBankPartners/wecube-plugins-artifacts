package com.webank.plugins.artifacts.interceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class ApiAccessInterceptor implements HandlerInterceptor {
    private static final String KEY_OF_USER_NAME = "username";
    private static final String DEFAULT_USER_NAME = "admin";

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String username = request.getHeader(KEY_OF_USER_NAME);
        if (username != null) {
            response.setHeader(KEY_OF_USER_NAME, username);
            UsernameStorage.getIntance().set(username);
        } else {
            // TO DO: Hard code for testing only, will remove later on
            // throw new PluginException("Required parameter 'roleName' is missing in
            // header.");
            response.setHeader(KEY_OF_USER_NAME, DEFAULT_USER_NAME);
            UsernameStorage.getIntance().set(DEFAULT_USER_NAME);
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        UsernameStorage.getIntance().remove();
    }
}
