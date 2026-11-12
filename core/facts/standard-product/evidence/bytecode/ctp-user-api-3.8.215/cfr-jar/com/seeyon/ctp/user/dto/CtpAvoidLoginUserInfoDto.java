/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import com.seeyon.ctp.user.dto.CtpUserSpiRedirectUrlDto;
import com.seeyon.ctp.user.dto.CtpUserSpiThirdTokenDto;
import java.io.Serializable;

@CtpUserComment(value="\u4e09\u65b9\u7528\u6237\u4fe1\u606f DTO")
public class CtpAvoidLoginUserInfoDto
implements Serializable {
    @CtpUserComment(value="\u4e09\u65b9\u7528\u6237ID, thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail \u6709\u4e14\u53ea\u6709\u4e00\u4e2a\u8d4b\u503c\u5373\u53ef\uff0c\u7528\u4e8e\u767b\u5f55v8\u7684\u552f\u4e00\u6761\u4ef6\u5b57\u6bb5")
    private String thirdUserId;
    @CtpUserComment(value="\u4e09\u65b9\u7528\u6237\u7f16\u7801, thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail \u6709\u4e14\u53ea\u6709\u4e00\u4e2a\u8d4b\u503c\u5373\u53ef\uff0c\u7528\u4e8e\u767b\u5f55v8\u7684\u552f\u4e00\u6761\u4ef6\u5b57\u6bb5")
    private String thirdUserCode;
    @CtpUserComment(value="\u4e09\u65b9\u7528\u6237\u624b\u673a\u53f7, thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail \u6709\u4e14\u53ea\u6709\u4e00\u4e2a\u8d4b\u503c\u5373\u53ef\uff0c\u7528\u4e8e\u767b\u5f55v8\u7684\u552f\u4e00\u6761\u4ef6\u5b57\u6bb5")
    private String thirdMobile;
    @CtpUserComment(value="\u4e09\u65b9\u7528\u6237\u767b\u5f55\u540d, thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail \u6709\u4e14\u53ea\u6709\u4e00\u4e2a\u8d4b\u503c\u5373\u53ef\uff0c\u7528\u4e8e\u767b\u5f55v8\u7684\u552f\u4e00\u6761\u4ef6\u5b57\u6bb5")
    private String thirdLoginName;
    @CtpUserComment(value="\u4e09\u65b9\u7528\u6237\u90ae\u7bb1, thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail \u6709\u4e14\u53ea\u6709\u4e00\u4e2a\u8d4b\u503c\u5373\u53ef\uff0c\u7528\u4e8e\u767b\u5f55v8\u7684\u552f\u4e00\u6761\u4ef6\u5b57\u6bb5")
    private String thirdUserEmail;
    @CtpUserComment(value="\u79df\u6237\u6570\u636e\u7c7b\u578b\uff1acode / id")
    private String tenantType;
    @CtpUserComment(value="\u79df\u6237\u6570\u636e\u503c\uff0c \u4e0e\u4e0a\u9762\u7c7b\u578b\u5bf9\u5e94")
    private String tenantData;
    @CtpUserComment(value="\u4e09\u65b9\u8ba4\u8bc1 token")
    private CtpUserSpiThirdTokenDto ctpUserSpiThirdTokenDto;
    @CtpUserComment(value="\u514d\u767b\u6210\u529f\u540e\u91cd\u5b9a\u5411\u5730\u5740")
    private CtpUserSpiRedirectUrlDto ctpUserSpiRedirectUrlDto;

    public static CtpAvoidLoginUserInfoDtoBuilder builder() {
        return new CtpAvoidLoginUserInfoDtoBuilder();
    }

    public String getThirdUserId() {
        return this.thirdUserId;
    }

    public String getThirdUserCode() {
        return this.thirdUserCode;
    }

    public String getThirdMobile() {
        return this.thirdMobile;
    }

    public String getThirdLoginName() {
        return this.thirdLoginName;
    }

    public String getThirdUserEmail() {
        return this.thirdUserEmail;
    }

    public String getTenantType() {
        return this.tenantType;
    }

    public String getTenantData() {
        return this.tenantData;
    }

    public CtpUserSpiThirdTokenDto getCtpUserSpiThirdTokenDto() {
        return this.ctpUserSpiThirdTokenDto;
    }

    public CtpUserSpiRedirectUrlDto getCtpUserSpiRedirectUrlDto() {
        return this.ctpUserSpiRedirectUrlDto;
    }

    public void setThirdUserId(String thirdUserId) {
        this.thirdUserId = thirdUserId;
    }

    public void setThirdUserCode(String thirdUserCode) {
        this.thirdUserCode = thirdUserCode;
    }

    public void setThirdMobile(String thirdMobile) {
        this.thirdMobile = thirdMobile;
    }

    public void setThirdLoginName(String thirdLoginName) {
        this.thirdLoginName = thirdLoginName;
    }

    public void setThirdUserEmail(String thirdUserEmail) {
        this.thirdUserEmail = thirdUserEmail;
    }

    public void setTenantType(String tenantType) {
        this.tenantType = tenantType;
    }

    public void setTenantData(String tenantData) {
        this.tenantData = tenantData;
    }

    public void setCtpUserSpiThirdTokenDto(CtpUserSpiThirdTokenDto ctpUserSpiThirdTokenDto) {
        this.ctpUserSpiThirdTokenDto = ctpUserSpiThirdTokenDto;
    }

    public void setCtpUserSpiRedirectUrlDto(CtpUserSpiRedirectUrlDto ctpUserSpiRedirectUrlDto) {
        this.ctpUserSpiRedirectUrlDto = ctpUserSpiRedirectUrlDto;
    }

    public String toString() {
        return "CtpAvoidLoginUserInfoDto(thirdUserId=" + this.getThirdUserId() + ", thirdUserCode=" + this.getThirdUserCode() + ", thirdMobile=" + this.getThirdMobile() + ", thirdLoginName=" + this.getThirdLoginName() + ", thirdUserEmail=" + this.getThirdUserEmail() + ", tenantType=" + this.getTenantType() + ", tenantData=" + this.getTenantData() + ", ctpUserSpiThirdTokenDto=" + this.getCtpUserSpiThirdTokenDto() + ", ctpUserSpiRedirectUrlDto=" + this.getCtpUserSpiRedirectUrlDto() + ")";
    }

    public CtpAvoidLoginUserInfoDto() {
    }

    public CtpAvoidLoginUserInfoDto(String thirdUserId, String thirdUserCode, String thirdMobile, String thirdLoginName, String thirdUserEmail, String tenantType, String tenantData, CtpUserSpiThirdTokenDto ctpUserSpiThirdTokenDto, CtpUserSpiRedirectUrlDto ctpUserSpiRedirectUrlDto) {
        this.thirdUserId = thirdUserId;
        this.thirdUserCode = thirdUserCode;
        this.thirdMobile = thirdMobile;
        this.thirdLoginName = thirdLoginName;
        this.thirdUserEmail = thirdUserEmail;
        this.tenantType = tenantType;
        this.tenantData = tenantData;
        this.ctpUserSpiThirdTokenDto = ctpUserSpiThirdTokenDto;
        this.ctpUserSpiRedirectUrlDto = ctpUserSpiRedirectUrlDto;
    }

    public static class CtpAvoidLoginUserInfoDtoBuilder {
        private String thirdUserId;
        private String thirdUserCode;
        private String thirdMobile;
        private String thirdLoginName;
        private String thirdUserEmail;
        private String tenantType;
        private String tenantData;
        private CtpUserSpiThirdTokenDto ctpUserSpiThirdTokenDto;
        private CtpUserSpiRedirectUrlDto ctpUserSpiRedirectUrlDto;

        CtpAvoidLoginUserInfoDtoBuilder() {
        }

        public CtpAvoidLoginUserInfoDtoBuilder thirdUserId(String thirdUserId) {
            this.thirdUserId = thirdUserId;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder thirdUserCode(String thirdUserCode) {
            this.thirdUserCode = thirdUserCode;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder thirdMobile(String thirdMobile) {
            this.thirdMobile = thirdMobile;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder thirdLoginName(String thirdLoginName) {
            this.thirdLoginName = thirdLoginName;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder thirdUserEmail(String thirdUserEmail) {
            this.thirdUserEmail = thirdUserEmail;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder tenantType(String tenantType) {
            this.tenantType = tenantType;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder tenantData(String tenantData) {
            this.tenantData = tenantData;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder ctpUserSpiThirdTokenDto(CtpUserSpiThirdTokenDto ctpUserSpiThirdTokenDto) {
            this.ctpUserSpiThirdTokenDto = ctpUserSpiThirdTokenDto;
            return this;
        }

        public CtpAvoidLoginUserInfoDtoBuilder ctpUserSpiRedirectUrlDto(CtpUserSpiRedirectUrlDto ctpUserSpiRedirectUrlDto) {
            this.ctpUserSpiRedirectUrlDto = ctpUserSpiRedirectUrlDto;
            return this;
        }

        public CtpAvoidLoginUserInfoDto build() {
            return new CtpAvoidLoginUserInfoDto(this.thirdUserId, this.thirdUserCode, this.thirdMobile, this.thirdLoginName, this.thirdUserEmail, this.tenantType, this.tenantData, this.ctpUserSpiThirdTokenDto, this.ctpUserSpiRedirectUrlDto);
        }

        public String toString() {
            return "CtpAvoidLoginUserInfoDto.CtpAvoidLoginUserInfoDtoBuilder(thirdUserId=" + this.thirdUserId + ", thirdUserCode=" + this.thirdUserCode + ", thirdMobile=" + this.thirdMobile + ", thirdLoginName=" + this.thirdLoginName + ", thirdUserEmail=" + this.thirdUserEmail + ", tenantType=" + this.tenantType + ", tenantData=" + this.tenantData + ", ctpUserSpiThirdTokenDto=" + this.ctpUserSpiThirdTokenDto + ", ctpUserSpiRedirectUrlDto=" + this.ctpUserSpiRedirectUrlDto + ")";
        }
    }
}

