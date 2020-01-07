package com.webank.plugins.artifacts.interceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class ApiAccessInterceptor implements HandlerInterceptor {
    private static final String KEY_OF_TOKEN = "Authorization";

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String authorization = request.getHeader(KEY_OF_TOKEN);
        if (authorization != null) {
            response.setHeader(KEY_OF_TOKEN, authorization);
            AuthorizationStorage.getIntance().set(authorization);
        } else {
            // TO DO: Hard code for testing only, will remove later on
            // throw new PluginException("Required parameter 'roleName' is missing in
            // header.");
            response.setHeader(KEY_OF_TOKEN, null);
            AuthorizationStorage.getIntance().set(KEY_OF_TOKEN);
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        AuthorizationStorage.getIntance().remove();
    }
}
