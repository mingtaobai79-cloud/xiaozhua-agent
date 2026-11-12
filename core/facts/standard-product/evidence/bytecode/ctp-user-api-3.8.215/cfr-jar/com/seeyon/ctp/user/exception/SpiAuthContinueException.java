/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.exception.BusinessException
 */
package com.seeyon.ctp.user.exception;

import com.seeyon.boot.exception.BusinessException;

public class SpiAuthContinueException
extends BusinessException {
    public SpiAuthContinueException() {
    }

    public SpiAuthContinueException(String code) {
        super(code);
    }

    public SpiAuthContinueException(String code, String ... params) {
        super(code, params);
    }

    public SpiAuthContinueException(String code, Throwable cause) {
        super(code, cause);
    }
}

