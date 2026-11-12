/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.ctp.user.enums;

import com.seeyon.boot.enums.Messageable;

public enum MenuPositionEnum implements Messageable
{
    HEAD(0),
    TAIL(2);

    private final int code;

    private MenuPositionEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}

