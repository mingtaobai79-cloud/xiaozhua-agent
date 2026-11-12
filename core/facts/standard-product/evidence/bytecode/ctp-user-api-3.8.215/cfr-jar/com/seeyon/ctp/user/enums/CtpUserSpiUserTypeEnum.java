/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.ctp.user.enums;

import com.seeyon.boot.enums.Messageable;

public enum CtpUserSpiUserTypeEnum implements Messageable
{
    INTERNAL(0),
    EXTERNAL(1),
    VISITOR(2),
    DEVICE(3),
    ROBOT(4),
    ADMINISTRATOR(5),
    OPENAPI(6),
    OPS(7),
    CLOUD(8),
    NATURAL_MEMBER(9),
    GUEST(10);

    private int code;

    private CtpUserSpiUserTypeEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}

