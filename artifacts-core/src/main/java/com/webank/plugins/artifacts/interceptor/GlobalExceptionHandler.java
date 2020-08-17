package com.webank.plugins.artifacts.interceptor;

import static com.webank.plugins.artifacts.domain.JsonResponse.error;

import java.util.Locale;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;

import com.webank.plugins.artifacts.commons.PluginException;
import com.webank.plugins.artifacts.domain.JsonResponse;


@ControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);
    
    public static final String MSG_ERR_CODE_PREFIX = "artifacts.core.msg.errorcode.";

    public static final Locale DEF_LOCALE = Locale.ENGLISH;

    @Autowired
    private MessageSource messageSource;
    
    
    @ExceptionHandler(PluginException.class)
    @ResponseBody
    public JsonResponse handleWecubeException(HttpServletRequest request, final Exception e,
            HttpServletResponse response) {
        String errMsg = String.format("Processing failed cause by %s:%s", e.getClass().getSimpleName(),
                e.getMessage() == null ? "" : e.getMessage());
        log.error(errMsg + "\n", e);
        PluginException wecubeError = (PluginException) e;

        return JsonResponse.error(determineI18nErrorMessage(request, wecubeError));
    }

    @ExceptionHandler(value = Exception.class)
    @ResponseBody
    public JsonResponse defaultErrorHandler(HttpServletRequest req, Exception e) throws Exception {
        log.error("errors occurred:", e);
        log.error("GlobalExceptionHandler: RequestHost {} invokes url {} ERROR: {}", req.getRemoteHost(), req.getRequestURL(), e.getMessage());
        return error(e.getMessage());
    }
    
    private String determineI18nErrorMessage(HttpServletRequest request, PluginException e) {
        Locale locale = request.getLocale();
        if (locale == null) {
            locale = DEF_LOCALE;
        }
        if (StringUtils.isNoneBlank(e.getErrorCode())) {
            String msgCode = MSG_ERR_CODE_PREFIX + e.getErrorCode();
            String msg = messageSource.getMessage(msgCode, e.getArgs(), locale);
            return msg;
        } else {
            return e.getMessage();
        }
    }

}
