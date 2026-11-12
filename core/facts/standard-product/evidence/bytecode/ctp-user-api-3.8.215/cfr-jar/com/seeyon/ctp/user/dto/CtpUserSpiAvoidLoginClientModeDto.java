/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.io.Serializable;
import java.util.Map;

@CtpUserComment(value="\u514d\u767b\u5904\u7406\u5165\u53c2")
public class CtpUserSpiAvoidLoginClientModeDto
implements Serializable {
    @CtpUserComment(value="\u7b2c\u4e09\u65b9\u7c7b\u578b\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 'c'")
    private String thirdType;
    @CtpUserComment(value="\u5ba2\u6237\u7aef\u7c7b\u578b, \u524d\u7aef\u81ea\u52a8\u8d4b\u503c\u3002eg: WEB | MOBILE")
    private String clientType;
    @CtpUserComment(value="\u65f6\u95f4\u6233_\u6beb\u79d2\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 't'")
    public String timestamp;
    @CtpUserComment(value="\u7b7e\u540d\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 's'")
    public String sign;
    @CtpUserComment(value="web\u7aef\u767b\u5f55\u5730\u5740\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 'w'")
    public String webUrl;
    @CtpUserComment(value="\u624b\u673a\u7aef\u767b\u5f55\u5730\u5740\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 'm'")
    public String mobileUrl;
    @CtpUserComment(value="\u52a0\u5bc6\u540e\u7684\u4e1a\u52a1\u6570\u636e\u3002 \u5bf9\u5e94\u524d\u7aef\u5165\u53c2\u4e2d\u7684 'd'")
    public String encryptData;
    @CtpUserComment(value="\u6269\u5c55\u6570\u636e")
    private Map<String, String> extData;

    public String getThirdType() {
        return this.thirdType;
    }

    public String getClientType() {
        return this.clientType;
    }

    public String getTimestamp() {
        return this.timestamp;
    }

    public String getSign() {
        return this.sign;
    }

    public String getWebUrl() {
        return this.webUrl;
    }

    public String getMobileUrl() {
        return this.mobileUrl;
    }

    public String getEncryptData() {
        return this.encryptData;
    }

    public Map<String, String> getExtData() {
        return this.extData;
    }

    public void setThirdType(String thirdType) {
        this.thirdType = thirdType;
    }

    public void setClientType(String clientType) {
        this.clientType = clientType;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public void setSign(String sign) {
        this.sign = sign;
    }

    public void setWebUrl(String webUrl) {
        this.webUrl = webUrl;
    }

    public void setMobileUrl(String mobileUrl) {
        this.mobileUrl = mobileUrl;
    }

    public void setEncryptData(String encryptData) {
        this.encryptData = encryptData;
    }

    public void setExtData(Map<String, String> extData) {
        this.extData = extData;
    }

    public String toString() {
        return "CtpUserSpiAvoidLoginClientModeDto(thirdType=" + this.getThirdType() + ", clientType=" + this.getClientType() + ", timestamp=" + this.getTimestamp() + ", sign=" + this.getSign() + ", webUrl=" + this.getWebUrl() + ", mobileUrl=" + this.getMobileUrl() + ", encryptData=" + this.getEncryptData() + ", extData=" + this.getExtData() + ")";
    }
}

