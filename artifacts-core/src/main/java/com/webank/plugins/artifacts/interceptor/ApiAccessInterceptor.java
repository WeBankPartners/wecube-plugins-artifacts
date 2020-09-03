package com.webank.plugins.artifacts.interceptor;

import java.security.Principal;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import com.webank.plugins.artifacts.constant.ArtifactsConstants;

@Component
public class ApiAccessInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(ApiAccessInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        
        
        Principal userPrincipal = request.getUserPrincipal();
        if (userPrincipal != null && (userPrincipal instanceof Authentication)) {
            String authorization = request.getHeader(ArtifactsConstants.KEY_OF_TOKEN);
            response.setHeader(ArtifactsConstants.KEY_OF_TOKEN, authorization);
            AuthorizationStorage.getIntance().set(authorization);
            
            Authentication auth = (Authentication)userPrincipal;
            request.setAttribute(ArtifactsConstants.UPLOAD_NAME, auth.getName());
            
            log.info("added token for {}", auth.getName());
        }else {
            log.info("remove token as there is none token presented.");
            AuthorizationStorage.getIntance().remove();
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        AuthorizationStorage.getIntance().remove();
    }
}
