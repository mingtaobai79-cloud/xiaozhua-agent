/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.constant;

import com.seeyon.ctp.user.annotation.CtpUserComment;

public class CtpUserSpiConstants {
    public static final String QR_CODE = "qrCode_";

    @Deprecated
    public static class DeviceType {
        public static final String MOBILE = "MOBILE";
        public static final String PC = "PC";
        public static final String PAD = "PAD";
        public static final String WEB = "WEB";
    }

    @CtpUserComment(value="\u767b\u5f55\u5ba2\u6237\u7aef\u7c7b\u578b")
    public static class ClientType {
        @CtpUserComment(value="Web\u6d4f\u89c8\u5668")
        public static final String WEB = "WEB";
        @CtpUserComment(value="PC\u684c\u9762\u7aef")
        public static final String PC = "PC";
        @CtpUserComment(value="\u624b\u673a\u79fb\u52a8\u7aef")
        public static final String MOBILE = "MOBILE";
        @CtpUserComment(value="\u624b\u673a\u79fb\u52a8\u7aef")
        public static final String PAD = "PAD";
        @CtpUserComment(value="\u7b2c\u4e09\u65b9")
        public static final String THIRD = "THIRD";
    }
}

