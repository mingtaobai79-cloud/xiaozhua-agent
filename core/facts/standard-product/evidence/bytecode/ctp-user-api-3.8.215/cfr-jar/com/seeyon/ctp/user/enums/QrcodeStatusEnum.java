/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.ctp.user.enums;

import com.seeyon.boot.enums.Messageable;

public enum QrcodeStatusEnum implements Messageable
{
    GENERATED(1),
    SCANNED_TODO(2),
    SCANNED(3),
    EXPIRED(4),
    ROUND(5);

    private final int code;

    private QrcodeStatusEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}

