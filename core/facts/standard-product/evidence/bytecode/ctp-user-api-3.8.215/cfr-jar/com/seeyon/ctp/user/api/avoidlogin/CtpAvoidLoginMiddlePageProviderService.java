/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.api.avoidlogin;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import com.seeyon.ctp.user.api.CtpSsoAvoidLoginBaseService;
import com.seeyon.ctp.user.dto.CtpAvoidLoginUserInfoDto;
import com.seeyon.ctp.user.dto.CtpUserSpiThirdTokenDto;
import com.seeyon.ctp.user.dto.ThirdTokenDto;
import java.util.Map;

@CtpUserComment(value="\u4e2d\u95f4\u9875\u8fdb\u884c\u514d\u767b")
public interface CtpAvoidLoginMiddlePageProviderService
extends CtpSsoAvoidLoginBaseService {
    @CtpUserComment(value="\u5b9a\u5236\u5316\u5904\u7406-\u4ece\u8bf7\u6c42\u4e2d\u63d0\u53d6\u53c2\u6570\u5e76\u83b7\u53d6\u7528\u6237\u4fe1\u606f")
    default public CtpAvoidLoginUserInfoDto getUserInfo(String code, Map<String, String> extData) {
        return null;
    }

    @CtpUserComment(value="\u81ea\u5b9a\u4e49\u67e5\u8be2\u83b7\u53d6 CtpUser \u5bf9\u8c61, \u901a\u8fc7\u53cd\u5c04\u67e5\u8be2\u7528\u6237\u4fe1\u606f\uff0c \u8fd4\u56de\u7684\u5fc5\u987b\u662f CtpUser \u5bf9\u8c61")
    default public Object getCtpUserInfo(String code, Map<String, String> extData) {
        return null;
    }

    @CtpUserComment(value="\u662f\u5426\u5468\u671f\u6027\u5237\u65b0 token")
    default public Boolean isRefreshTokenCycle() {
        return false;
    }

    @CtpUserComment(value="\u5237\u65b0\u4e09\u65b9 token")
    default public CtpUserSpiThirdTokenDto doRefreshToken(ThirdTokenDto thirdTokenDto) {
        return null;
    }
}

