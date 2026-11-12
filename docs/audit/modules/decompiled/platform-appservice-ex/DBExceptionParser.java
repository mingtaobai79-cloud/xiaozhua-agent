/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.exception.BusinessException
 */
package com.seeyon.boot.starter.appservice.ex.parser;

import com.seeyon.boot.exception.BusinessException;

public interface DBExceptionParser {
    public BusinessException parser(String var1);
}
