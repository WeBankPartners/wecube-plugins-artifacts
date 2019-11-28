package com.webank.plugins.artifacts.commons;

public class WecubeCoreException extends RuntimeException {
    /**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public WecubeCoreException(String message) {
        super(message);
    }

    public WecubeCoreException(String message, Throwable cause) {
        super(message, cause);
    }
}
