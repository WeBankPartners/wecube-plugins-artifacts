package com.webank.plugins.artifacts.support.saltstack;

public class SaltFileNotExistException extends RuntimeException {

    /**
     * 
     */
    private static final long serialVersionUID = 5974905083999742131L;

    public SaltFileNotExistException() {
        super();
    }

    public SaltFileNotExistException(String message, Throwable cause, boolean enableSuppression,
            boolean writableStackTrace) {
        super(message, cause, enableSuppression, writableStackTrace);
    }

    public SaltFileNotExistException(String message, Throwable cause) {
        super(message, cause);
    }

    public SaltFileNotExistException(String message) {
        super(message);
    }

    public SaltFileNotExistException(Throwable cause) {
        super(cause);
    }
    
    

}
