/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.bpm.enums;

import com.seeyon.boot.enums.Messageable;

public enum OperateTypeEnum implements Messageable
{
    NONE(0),
    OPERATE_TYPE_ADD(1),
    OPERATE_TYPE_JOINTLY(2),
    OPERATE_USER_BACK(3),
    OPERATE_TYPE_NOTICE(4);

    private int code;

    private OperateTypeEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}
