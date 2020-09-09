package com.webank.plugins.artifacts.support.cmdb.dto;

public class StandardCmdbEntityResponseDto {
    public final static String STATUS_OK = "OK";
    public final static String STATUS_ERROR = "ERROR";

    private String status;
    private String message;
    private Object data;

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Object getData() {
        return data;
    }

    public void setData(Object data) {
        this.data = data;
    }

    public StandardCmdbEntityResponseDto withData(Object data){
        this.data = data;
        return this;
    }

    public static StandardCmdbEntityResponseDto okay() {
        StandardCmdbEntityResponseDto result = new StandardCmdbEntityResponseDto();
        result.setStatus(STATUS_OK);
        result.setMessage("Success");
        return result;
    }

    public static StandardCmdbEntityResponseDto okayWithData(Object data) {
        return okay().withData(data);
    }

    public static StandardCmdbEntityResponseDto error(String errorMessage) {
        StandardCmdbEntityResponseDto result = new StandardCmdbEntityResponseDto();
        result.setStatus(STATUS_ERROR);
        result.setMessage(errorMessage);
        return result;
    }

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder();
        builder.append("[status=");
        builder.append(status);
        builder.append(", message=");
        builder.append(message);
        builder.append(", data=");
        builder.append(data);
        builder.append("]");
        return builder.toString();
    }
    
    
}
