package com.webank.plugins.artifacts.interceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import com.webank.plugins.artifacts.constant.ArtifactsConstants;
import com.webank.plugins.artifacts.utils.JwtUtils;

@Component
public class ApiAccessInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String authorization = request.getHeader(ArtifactsConstants.KEY_OF_TOKEN);
        request.setAttribute(ArtifactsConstants.UPLOAD_NAME, JwtUtils.getAuthUserName(authorization));
        if (authorization != null) {
            response.setHeader(ArtifactsConstants.KEY_OF_TOKEN, authorization);
            AuthorizationStorage.getIntance().set(authorization);
        } else {
            response.setHeader(ArtifactsConstants.KEY_OF_TOKEN, null);
            AuthorizationStorage.getIntance().set(ArtifactsConstants.KEY_OF_TOKEN);
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        AuthorizationStorage.getIntance().remove();
    }
}
