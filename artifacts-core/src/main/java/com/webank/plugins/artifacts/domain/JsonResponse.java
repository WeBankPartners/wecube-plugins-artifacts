package com.webank.plugins.artifacts.domain;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class JsonResponse {
    public final static String STATUS_OK = "OK";
    public final static String STATUS_ERROR = "ERROR";

    private String status;
    private String message;
    private Object data;

    public JsonResponse withData(Object data) {
        this.data = data;
        return this;
    }

    public static JsonResponse okay() {
        JsonResponse result = new JsonResponse();
        result.setStatus(STATUS_OK);
        result.setMessage("Success");
        return result;
    }

    public static JsonResponse okayWithData(Object data) {
        return okay().withData(data);
    }

    public static JsonResponse error(String errorMessage) {
        JsonResponse result = new JsonResponse();
        result.setStatus(STATUS_ERROR);
        result.setMessage(errorMessage);
        return result;
    }
}
