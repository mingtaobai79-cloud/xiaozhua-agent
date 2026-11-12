/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.http.HttpServletRequest
 *  javax.servlet.http.HttpServletResponse
 */
package com.seeyon.ctp.user.api.avoidlogin;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import com.seeyon.ctp.user.api.CtpSsoAvoidLoginBaseService;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@CtpUserComment(value="\u540e\u7aef\u76f4\u63a5\u8bf7\u6c42\u8fdb\u884c\u514d\u767b")
public interface CtpAvoidLoginBackendProviderService
extends CtpSsoAvoidLoginBaseService {
    @Deprecated
    default public Map<String, Object> doExecuteAvoidLoginBackend(HttpServletRequest request, HttpServletResponse response) {
        return null;
    }

    @CtpUserComment(value="\u540e\u7aef\u8bf7\u6c42\u903b\u8f91")
    default public Object avoidLoginBackend(HttpServletRequest request, HttpServletResponse response) {
        return null;
    }
}

