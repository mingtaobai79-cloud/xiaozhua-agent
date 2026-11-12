/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.io.Serializable;
import java.util.Map;

@CtpUserComment(value="\u4e09\u65b9 token \u4fdd\u5b58 DTO")
public class CtpUserSpiThirdTokenDto
implements Serializable {
    @CtpUserComment(value="\u5f85\u7f13\u5b58\u7684\u4e09\u65b9 token")
    private String thirdToken;
    @CtpUserComment(value="\u8fc7\u671f\u65f6\u95f4_\u79d2")
    private Long expired;
    @CtpUserComment(value="\u6269\u5c55\u53c2\u6570")
    private Map<String, Object> extData;

    public static CtpUserSpiThirdTokenDtoBuilder builder() {
        return new CtpUserSpiThirdTokenDtoBuilder();
    }

    public String getThirdToken() {
        return this.thirdToken;
    }

    public Long getExpired() {
        return this.expired;
    }

    public Map<String, Object> getExtData() {
        return this.extData;
    }

    public void setThirdToken(String thirdToken) {
        this.thirdToken = thirdToken;
    }

    public void setExpired(Long expired) {
        this.expired = expired;
    }

    public void setExtData(Map<String, Object> extData) {
        this.extData = extData;
    }

    public String toString() {
        return "CtpUserSpiThirdTokenDto(thirdToken=" + this.getThirdToken() + ", expired=" + this.getExpired() + ", extData=" + this.getExtData() + ")";
    }

    public CtpUserSpiThirdTokenDto() {
    }

    public CtpUserSpiThirdTokenDto(String thirdToken, Long expired, Map<String, Object> extData) {
        this.thirdToken = thirdToken;
        this.expired = expired;
        this.extData = extData;
    }

    public static class CtpUserSpiThirdTokenDtoBuilder {
        private String thirdToken;
        private Long expired;
        private Map<String, Object> extData;

        CtpUserSpiThirdTokenDtoBuilder() {
        }

        public CtpUserSpiThirdTokenDtoBuilder thirdToken(String thirdToken) {
            this.thirdToken = thirdToken;
            return this;
        }

        public CtpUserSpiThirdTokenDtoBuilder expired(Long expired) {
            this.expired = expired;
            return this;
        }

        public CtpUserSpiThirdTokenDtoBuilder extData(Map<String, Object> extData) {
            this.extData = extData;
            return this;
        }

        public CtpUserSpiThirdTokenDto build() {
            return new CtpUserSpiThirdTokenDto(this.thirdToken, this.expired, this.extData);
        }

        public String toString() {
            return "CtpUserSpiThirdTokenDto.CtpUserSpiThirdTokenDtoBuilder(thirdToken=" + this.thirdToken + ", expired=" + this.expired + ", extData=" + this.extData + ")";
        }
    }
}

