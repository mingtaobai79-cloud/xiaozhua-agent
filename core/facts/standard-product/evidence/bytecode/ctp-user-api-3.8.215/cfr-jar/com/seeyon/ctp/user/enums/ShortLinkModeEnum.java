/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.ctp.user.enums;

import com.seeyon.boot.enums.Messageable;
import com.seeyon.ctp.user.annotation.CtpUserComment;

@CtpUserComment(value="\u77ed\u94fe\u6a21\u5f0f")
public enum ShortLinkModeEnum implements Messageable
{
    COMPACT_MODE(1),
    SPLICING_MODE(2);

    private final int code;

    private ShortLinkModeEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}

