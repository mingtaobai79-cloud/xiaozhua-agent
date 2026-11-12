/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.io.Serializable;

@CtpUserComment(value="ctp-user \u670d\u52a1\u73af\u5883\u914d\u7f6e\u4fe1\u606f")
public class CtpUserSpiServerEnvDto
implements Serializable {
    @CtpUserComment(value="\u670d\u52a1\u57df\u540d")
    private String serverDomain;
    @CtpUserComment(value="\u524d\u7aef\u5730\u5740\u8def\u7531")
    private String frontBaseRoute;

    CtpUserSpiServerEnvDto(String serverDomain, String frontBaseRoute) {
        this.serverDomain = serverDomain;
        this.frontBaseRoute = frontBaseRoute;
    }

    public static CtpUserSpiServerEnvDtoBuilder builder() {
        return new CtpUserSpiServerEnvDtoBuilder();
    }

    public String getServerDomain() {
        return this.serverDomain;
    }

    public String getFrontBaseRoute() {
        return this.frontBaseRoute;
    }

    public String toString() {
        return "CtpUserSpiServerEnvDto(serverDomain=" + this.getServerDomain() + ", frontBaseRoute=" + this.getFrontBaseRoute() + ")";
    }

    public static class CtpUserSpiServerEnvDtoBuilder {
        private String serverDomain;
        private String frontBaseRoute;

        CtpUserSpiServerEnvDtoBuilder() {
        }

        public CtpUserSpiServerEnvDtoBuilder serverDomain(String serverDomain) {
            this.serverDomain = serverDomain;
            return this;
        }

        public CtpUserSpiServerEnvDtoBuilder frontBaseRoute(String frontBaseRoute) {
            this.frontBaseRoute = frontBaseRoute;
            return this;
        }

        public CtpUserSpiServerEnvDto build() {
            return new CtpUserSpiServerEnvDto(this.serverDomain, this.frontBaseRoute);
        }

        public String toString() {
            return "CtpUserSpiServerEnvDto.CtpUserSpiServerEnvDtoBuilder(serverDomain=" + this.serverDomain + ", frontBaseRoute=" + this.frontBaseRoute + ")";
        }
    }
}

