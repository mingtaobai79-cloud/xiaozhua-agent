/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.io.Serializable;

@CtpUserComment(value="\u4e09\u65b9 token \u4fdd\u5b58 DTO")
public class ThirdTokenDto
implements Serializable {
    private String innerUserId;
    private String thirdToken;

    public static ThirdTokenDtoBuilder builder() {
        return new ThirdTokenDtoBuilder();
    }

    public String getInnerUserId() {
        return this.innerUserId;
    }

    public String getThirdToken() {
        return this.thirdToken;
    }

    public void setInnerUserId(String innerUserId) {
        this.innerUserId = innerUserId;
    }

    public void setThirdToken(String thirdToken) {
        this.thirdToken = thirdToken;
    }

    public String toString() {
        return "ThirdTokenDto(innerUserId=" + this.getInnerUserId() + ", thirdToken=" + this.getThirdToken() + ")";
    }

    public ThirdTokenDto() {
    }

    public ThirdTokenDto(String innerUserId, String thirdToken) {
        this.innerUserId = innerUserId;
        this.thirdToken = thirdToken;
    }

    public static class ThirdTokenDtoBuilder {
        private String innerUserId;
        private String thirdToken;

        ThirdTokenDtoBuilder() {
        }

        public ThirdTokenDtoBuilder innerUserId(String innerUserId) {
            this.innerUserId = innerUserId;
            return this;
        }

        public ThirdTokenDtoBuilder thirdToken(String thirdToken) {
            this.thirdToken = thirdToken;
            return this;
        }

        public ThirdTokenDto build() {
            return new ThirdTokenDto(this.innerUserId, this.thirdToken);
        }

        public String toString() {
            return "ThirdTokenDto.ThirdTokenDtoBuilder(innerUserId=" + this.innerUserId + ", thirdToken=" + this.thirdToken + ")";
        }
    }
}

