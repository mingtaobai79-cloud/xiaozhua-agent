/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.io.Serializable;

@CtpUserComment(value="\u514d\u767b\u6210\u529f\u540e\u91cd\u5b9a\u5411\u5730\u5740")
public class CtpUserSpiRedirectUrlDto
implements Serializable {
    @CtpUserComment(value="web \u91cd\u5b9a\u5411\u5730\u5740")
    private String webRedirectUrl;
    @CtpUserComment(value="mobile \u91cd\u5b9a\u5411\u5730\u5740")
    private String mobileRedirectUrl;

    public static CtpUserSpiRedirectUrlDtoBuilder builder() {
        return new CtpUserSpiRedirectUrlDtoBuilder();
    }

    public String getWebRedirectUrl() {
        return this.webRedirectUrl;
    }

    public String getMobileRedirectUrl() {
        return this.mobileRedirectUrl;
    }

    public void setWebRedirectUrl(String webRedirectUrl) {
        this.webRedirectUrl = webRedirectUrl;
    }

    public void setMobileRedirectUrl(String mobileRedirectUrl) {
        this.mobileRedirectUrl = mobileRedirectUrl;
    }

    public String toString() {
        return "CtpUserSpiRedirectUrlDto(webRedirectUrl=" + this.getWebRedirectUrl() + ", mobileRedirectUrl=" + this.getMobileRedirectUrl() + ")";
    }

    public CtpUserSpiRedirectUrlDto() {
    }

    public CtpUserSpiRedirectUrlDto(String webRedirectUrl, String mobileRedirectUrl) {
        this.webRedirectUrl = webRedirectUrl;
        this.mobileRedirectUrl = mobileRedirectUrl;
    }

    public static class CtpUserSpiRedirectUrlDtoBuilder {
        private String webRedirectUrl;
        private String mobileRedirectUrl;

        CtpUserSpiRedirectUrlDtoBuilder() {
        }

        public CtpUserSpiRedirectUrlDtoBuilder webRedirectUrl(String webRedirectUrl) {
            this.webRedirectUrl = webRedirectUrl;
            return this;
        }

        public CtpUserSpiRedirectUrlDtoBuilder mobileRedirectUrl(String mobileRedirectUrl) {
            this.mobileRedirectUrl = mobileRedirectUrl;
            return this;
        }

        public CtpUserSpiRedirectUrlDto build() {
            return new CtpUserSpiRedirectUrlDto(this.webRedirectUrl, this.mobileRedirectUrl);
        }

        public String toString() {
            return "CtpUserSpiRedirectUrlDto.CtpUserSpiRedirectUrlDtoBuilder(webRedirectUrl=" + this.webRedirectUrl + ", mobileRedirectUrl=" + this.mobileRedirectUrl + ")";
        }
    }
}

