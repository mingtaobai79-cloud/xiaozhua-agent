/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.ctp.user.enums;

import com.seeyon.boot.enums.Messageable;

public enum CtpUserSpiAuthTokenEnum implements Messageable
{
    SPI_SSO(0, "com.seeyon.ctp.user.security.authentication.SpiSsoAuthenticationToken"),
    USERNAME_PASSWORD(1, "com.seeyon.ctp.user.security.authentication.UsernamePasswordAuthenticationToken"),
    PHONE_VERIFY_CODE(2, "com.seeyon.ctp.user.security.authentication.PhoneNumberDynamicPasswordAuthenticationToken");

    private int code;
    private String className;

    private CtpUserSpiAuthTokenEnum(int code, String className) {
        this.code = code;
        this.className = className;
    }

    public int code() {
        return this.code;
    }

    public String getClassName() {
        return this.className;
    }
}

