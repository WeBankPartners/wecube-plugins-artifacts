package com.webank.plugins.artifacts.interceptor;

import com.webank.plugins.artifacts.domain.JsonResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;

import javax.servlet.http.HttpServletRequest;

import static com.webank.plugins.artifacts.domain.JsonResponse.error;


@ControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(value = Exception.class)
    @ResponseBody
    public JsonResponse defaultErrorHandler(HttpServletRequest req, Exception e) throws Exception {
        log.error("errors occurred:", e);
        log.error("GlobalExceptionHandler: RequestHost {} invokes url {} ERROR: {}", req.getRemoteHost(), req.getRequestURL(), e.getMessage());
        return error(e.getMessage());
    }

}
