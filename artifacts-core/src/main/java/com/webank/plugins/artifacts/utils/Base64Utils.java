package com.webank.plugins.artifacts.utils;

import sun.misc.BASE64Decoder;

public class Base64Utils {

    public static String getBASE64(String s) {
        if (s == null) return null;
        return (new sun.misc.BASE64Encoder()).encode(s.getBytes());
    }

    public static String getFromBASE64(String s) {
        if (s == null) return null;
        BASE64Decoder decoder = new BASE64Decoder();
        try {
            byte[] b = decoder.decodeBuffer(s);
            return new String(b);
        } catch (Exception e) {
            return null;
        }
    }

    public static void main(String[] args) {
        //String str = "123456";
        System.out.println(Base64Utils.getBASE64("admin" + ":" + "admin1234"));
    }
}
