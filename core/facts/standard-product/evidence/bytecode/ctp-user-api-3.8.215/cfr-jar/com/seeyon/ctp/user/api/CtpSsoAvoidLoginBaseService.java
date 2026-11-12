/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.api;

import com.seeyon.ctp.user.annotation.CtpUserComment;

public interface CtpSsoAvoidLoginBaseService {
    public static final String TAG = "[avoid]";

    @CtpUserComment(value="\u8fd4\u56de\u5ba2\u6237\u7aef\u6807\u8bc6\uff0c\u53cc\u65b9\u7ea6\u5b9a\u7684\u552f\u4e00 type")
    public String getClientId();
}

