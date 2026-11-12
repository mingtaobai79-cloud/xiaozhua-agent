/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.http.HttpServletRequest
 *  org.apache.commons.collections.CollectionUtils
 */
package com.seeyon.ctp.user.api.sso;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import com.seeyon.ctp.user.dto.CtpUserSpiLoginUserInfoDto;
import com.seeyon.ctp.user.dto.CtpUserSpiServerEnvDto;
import com.seeyon.ctp.user.dto.CtpUserSpiThirdTokenDto;
import com.seeyon.ctp.user.dto.CtpUserSpiUserDto;
import com.seeyon.ctp.user.enums.CtpUserSpiAuthTokenEnum;
import com.seeyon.ctp.user.enums.ShortLinkModeEnum;
import com.seeyon.ctp.user.exception.CtpUserSpiSsoException;
import com.seeyon.ctp.user.exception.SpiAuthContinueException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import org.apache.commons.collections.CollectionUtils;

@CtpUserComment(value="\u7edf\u4e00\u4e09\u65b9\u8ba4\u8bc1 SPI \u6269\u5c55\u63a5\u53e3, \u5b9e\u73b0\u7c7b\u9700\u8981\u589e\u52a0 @CtpUserChannelRouter \u6ce8\u89e3")
public interface CtpUserSsoAuthProviderService {
    @Deprecated
    @CtpUserComment(value="\u8bbe\u7f6e\u670d\u52a1\u5668\u7684\u57df\u540d")
    default public void setServerDomain(String serverDomain) {
    }

    @CtpUserComment(value="\u8bbe\u7f6e\u670d\u52a1\u73af\u5883\u914d\u7f6e\u4fe1\u606f, \u5982\u57df\u540d\u53ca\u524d\u7aef\u5730\u5740\u8def\u7531\u7b49")
    default public void setServerEnv(CtpUserSpiServerEnvDto ctpUserSpiServerEnvDto) {
    }

    @CtpUserComment(value="\u4ece request \u4e2d\u83b7\u53d6\u4e34\u65f6 code \u6216 ticket \u7684 key, \u5982\u679c\u767b\u5f55\u540e\u5728\u91cd\u5b9a\u5411\u5730\u5740\u540e\u8ffd\u52a0\u7684 key \u53eb code\uff0c\u8fd9\u91cc\u8fd4\u56de code\uff1b \u5982\u679c\u8ffd\u52a0\u503c key \u53eb ticket\uff0c \u8fd9\u91cc\u8fd4\u56de ticket")
    public String getRequestParaKey();

    @CtpUserComment(value="\u4e09\u65b9\u8ba4\u8bc1 sso \u767b\u5f55\u5730\u5740")
    public String getSsoLoginUrl(HttpServletRequest var1, String var2);

    @CtpUserComment(value="\u4e09\u65b9\u8ba4\u8bc1\u53d1\u9001\u77ed\u4fe1\u9a8c\u8bc1\u7801")
    default public Boolean sendVerifyCode(String mobile) {
        return null;
    }

    @Deprecated
    @CtpUserComment(value="\u767b\u5f55\u4e09\u65b9\u6210\u529f\u540e\u7684\u91cd\u5b9a\u5411\u5730\u5740\u662f\u5426\u4f7f\u7528\u77ed\u94fe\u63a5")
    default public Boolean isRedirectShortLink() {
        return false;
    }

    @CtpUserComment(value="\u767b\u5f55\u4e09\u65b9\u6210\u529f\u540e\u7684\u91cd\u5b9a\u5411\u5730\u5740\u662f\u5426\u4f7f\u7528\u77ed\u94fe\u63a5\u53ca\u77ed\u94fe\u63a5\u6a21\u5f0f\uff0c\u5982\u679c\u8bbe\u7f6e\u4e86\u6a21\u5f0f\uff0c\u81ea\u52a8\u5f00\u542f\u77ed\u94fe")
    default public ShortLinkModeEnum shortLinkMode() {
        return null;
    }

    @CtpUserComment(value="\u4ece\u4e09\u65b9\u8ba4\u8bc1\u63a5\u53e3\u4e2d\u83b7\u53d6\u7528\u6237\u4fe1\u606f\uff0c\u5982 oauth2 \u6a21\u5f0f\u4e0b\uff0c \u4ece request \u91cc\u83b7\u53d6\u5230 code\uff0c\u901a\u8fc7 code \u83b7\u53d6\u5230\u7b2c\u4e09\u65b9\u8ba4\u8bc1\u7684 token\uff0c\u901a\u8fc7 token \u83b7\u53d6\u5230\u53cc\u65b9\u4e00\u81f4\u7684\u7528\u6237\u4fe1\u606f\u3002\u5982\u679c\u767b\u5f55\u5f02\u5e38\u63d0\u793a\u60f3\u8981\u63d0\u793a\u5728\u9875\u9762\u4e0a\uff0c\u5219\u4f7f\u7528 CtpUserSpiSsoException \u629b\u51fa\uff0c\u63d0\u793a\u5185\u5bb9\u4e3a CtpUserSpiSsoException \u91cc\u7684 message \u7684\u503c")
    public CtpUserSpiLoginUserInfoDto getUserLoginInfo(HttpServletRequest var1, String var2) throws CtpUserSpiSsoException, SpiAuthContinueException;

    @CtpUserComment(value="\u4e09\u65b9\u767b\u51fa\u91cd\u5b9a\u5411\u5730\u5740\uff0c \u4e09\u65b9\u8ba4\u8bc1\u4e2d\u5fc3\u53ef\u901a\u8fc7\u6b64\u5730\u5740\u8fdb\u884c\u7528\u6237\u767b\u5f55\u64cd\u4f5c\uff0c\u5982\u679c\u6ca1\u6709\u6b64\u63a5\u53e3\uff0c\u5219\u4e0d\u7528\u5b9e\u73b0")
    default public String getEncodeLogoutRedirectUrl() {
        return null;
    }

    @CtpUserComment(value="\u4e09\u65b9\u8ba4\u8bc1 sso \u767b\u51fa\u903b\u8f91\uff0c \u6309\u9700\u6c42\u5b9e\u73b0\u3002 \u5982\u679c\u9700\u8981\u767b\u5f55\u7684\u8ba4\u8bc1\uff0c\u540c\u65f6 getEncodeLogoutRedirectUrl \u65b9\u6cd5\u53ef\u4ee5\u4f7f\u7528\uff0c\u5219\u6b64\u65b9\u6cd5\u4e0d\u7528\u5b9e\u73b0")
    default public void thirdSsoLogout(HttpServletRequest request, String thirdUserInfoJson) {
    }

    @CtpUserComment(value="\u624b\u673a\u7aef\u767b\u5f55\u4f7f\u7528\uff0c\u901a\u8fc7\u7528\u6237\u540d\u5bc6\u7801\u7b49\u4fe1\u606f\u8ba4\u8bc1\u5e76\u83b7\u53d6\u767b\u5f55\u540d\u3002 \u624b\u673a\u7aef\u76f4\u63a5\u8c03\u7528\u5411\u540e\u7aef\u5165\u53c2\u5185\u5bb9\u3002\u5982\u679c\u767b\u5f55\u5f02\u5e38\u63d0\u793a\u60f3\u8981\u63d0\u793a\u5728\u9875\u9762\u4e0a\uff0c\u5219\u4f7f\u7528 CtpUserSpiSsoException \u629b\u51fa\uff0c\u63d0\u793a\u5185\u5bb9\u4e3a CtpUserSpiSsoException \u91cc\u7684 message \u7684\u503c")
    default public CtpUserSpiLoginUserInfoDto getUserLoginInfoForMobile(String userLoginName, Map<String, Object> extData, CtpUserSpiAuthTokenEnum ctpUserSpiAuthTokenEnum) throws CtpUserSpiSsoException {
        return null;
    }

    @CtpUserComment(value="\u5982\u679c v8 token \u8fc7\u671f\uff0c\u5219\u8d4b\u503c\u7a7a\uff0c \u53ef\u4ee5\u91cd\u65b0\u4f7f\u7528\u4e09\u65b9\u8ba4\u8bc1\u4e2d\u5fc3\u767b\u5f55\u9875\u767b\u5f55")
    default public boolean tokenExpiredSetNull() {
        return false;
    }

    @CtpUserComment(value="\u5982\u679c\u83b7\u53d6\u5230\u591a\u4e2a ctpUserDto \uff0c\u5219\u4e1a\u52a1\u65b9\u5224\u65ad\u53d6\u54ea\u4e2a\uff0c \u9ed8\u8ba4\u53d6\u7b2c\u4e00\u4e2a")
    default public Long rebuildCtpUserDtoList(List<CtpUserSpiUserDto> ctpUserSpiUserDtoList) {
        if (CollectionUtils.isEmpty(ctpUserSpiUserDtoList)) {
            return null;
        }
        return ctpUserSpiUserDtoList.get(0).getId();
    }

    @Deprecated
    default public CtpUserSpiThirdTokenDto refreshThirdToken(String thirdToken, long expired) {
        return null;
    }

    @CtpUserComment(value="\u5237\u65b0\u4e09\u65b9 token")
    default public CtpUserSpiThirdTokenDto refreshThirdTokenByConfig(String thirdToken, Map<String, Object> thirdTokenConfigMap) {
        return null;
    }

    @CtpUserComment(value="\u5982\u679c\u9700\u8981\u7f13\u5b58 4a token\uff0c\u5219\u8fd4\u56de key")
    default public String get4aTokenKey() {
        return null;
    }

    @CtpUserComment(value="\u4e3a\u4e0a\u4e0b\u6587\u79df\u6237\u8d4b\u503c\uff0c \u901a\u8fc7code \u83b7\u53d6\u4e0a\u4e0b\u6587\u79df\u6237")
    default public String getTidCode() {
        return null;
    }

    @CtpUserComment(value="\u767b\u5f55\u8ba4\u8bc1\u6761\u4ef6, \u8fd4\u56de\u503c map: key \u767b\u5f55\u8bbe\u5907\u7c7b\u578b\u7684\u503c(WEB/PC/MOBILE), value: \u767b\u5f55\u65b9\u5f0f\u3002 \u9ed8\u8ba4\u5904\u7406 pc:CtpUserSpiAuthTokenEnum.SPI_SSO \u7c7b\u578b")
    default public Map<String, CtpUserSpiAuthTokenEnum[]> mapSupportsAuthTokenEnum() {
        HashMap<String, CtpUserSpiAuthTokenEnum[]> loginTokenEnumMap = new HashMap<String, CtpUserSpiAuthTokenEnum[]>();
        loginTokenEnumMap.put("WEB", new CtpUserSpiAuthTokenEnum[]{CtpUserSpiAuthTokenEnum.SPI_SSO});
        return loginTokenEnumMap;
    }

    @CtpUserComment(value="\u9ed8\u8ba4\u8fd4\u56de CtpUserSpiAuthToken.USERNAME_PASSWORD")
    default public CtpUserSpiAuthTokenEnum getSuccessAuthTokenEnum() {
        return CtpUserSpiAuthTokenEnum.USERNAME_PASSWORD;
    }
}

