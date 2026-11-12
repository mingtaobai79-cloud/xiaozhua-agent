/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.constant;

import com.seeyon.ctp.user.annotation.CtpUserComment;

public class CtpUserSpiAvoidConstants {

    @CtpUserComment(value="\u52a0\u5bc6\u7b7e\u540d\u7b97\u6cd5\u540d\u79f0")
    public static class KeyMethodName {
        public static final String RSA = "RSA";
        public static final String AES = "AES";
        public static final String DES = "DES";
        public static final String MD5 = "MD5";
        public static final String SHA1 = "SHA1";
        public static final String SHA256 = "SHA256";
    }

    @CtpUserComment(value="\u4e1a\u52a1\u6570\u636ekey")
    public static class DataKey {
        @CtpUserComment(value="\u767b\u5f55\u540d")
        public static final String USER_LOGIN_NAME = "l";
        @CtpUserComment(value="\u624b\u673a\u53f7")
        public static final String USER_MOBILE = "m";
        @CtpUserComment(value="\u7528\u6237\u7f16\u7801")
        public static final String USER_CODE = "c";
    }
}

