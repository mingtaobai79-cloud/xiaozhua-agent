/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.api.avoidlogin;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import com.seeyon.ctp.user.api.CtpSsoAvoidLoginBaseService;
import com.seeyon.ctp.user.dto.CtpAvoidLoginUserInfoDto;
import com.seeyon.ctp.user.dto.CtpUserSpiAvoidLoginClientModeDto;
import com.seeyon.ctp.user.exception.CtpUserSpiSsoException;

@CtpUserComment(value="\u5ba2\u6237\u7aef\u76f4\u63a5\u514d\u767b")
public interface CtpAvoidLoginClientModeProviderService
extends CtpSsoAvoidLoginBaseService {
    @CtpUserComment(value="\u53c2\u6570\u9a8c\u8bc1, \u5982\u679c\u9a8c\u8bc1\u5931\u8d25\uff0c\u629b\u51fa CtpUserSpiSsoException \u5f02\u5e38")
    public void preCheck(CtpUserSpiAvoidLoginClientModeDto var1) throws CtpUserSpiSsoException;

    @CtpUserComment(value="\u83b7\u53d6\u7528\u6237\u4fe1\u606f")
    public CtpAvoidLoginUserInfoDto getUserInfo(CtpUserSpiAvoidLoginClientModeDto var1);
}

