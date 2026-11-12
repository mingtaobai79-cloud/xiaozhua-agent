/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.AppService$ValidationGroup$Create
 *  com.seeyon.boot.annotation.AppService$ValidationGroup$Update
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  javax.validation.constraints.NotBlank
 *  javax.validation.constraints.NotNull
 *  javax.validation.constraints.Size
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.boot.annotation.AppService;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.ctp.user.enums.CtpUserSpiUserTypeEnum;
import java.util.Date;
import java.util.List;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@DtoInfo(value="\u7528\u6237\u4fe1\u606f")
public class CtpUserSpiUserDto
extends BaseDto {
    @DtoAttribute(value="\u7528\u6237ID", example="60828711522402304")
    @NotNull(groups={AppService.ValidationGroup.Update.class})
    private Long id;
    @DtoAttribute(value="\u79df\u6237\u6807\u8bc6", hidden=true)
    private Long tenantId;
    @DtoAttribute(value="\u7528\u6237\u540d\u79f0", example="\u5f20\u4e09")
    @NotBlank(groups={AppService.ValidationGroup.Create.class})
    private String name;
    @DtoAttribute(value="\u767b\u5f55\u540d", example="zhangsan")
    @NotBlank
    @Size(max=50)
    private @NotBlank @Size(max=50) String loginName;
    @DtoAttribute(value="\u5bc6\u7801", example="123456")
    @Size(max=100)
    private @Size(max=100) String password;
    @DtoAttribute(value="\u5bc6\u7801\u8fc7\u671f\u65f6\u95f4", example="1637480629922")
    private Date expiredTime;
    @DtoAttribute(value="\u5934\u50cf", example="60828711522402304")
    @Size(max=150)
    private @Size(max=150) String avatar;
    @DtoAttribute(value="\u624b\u673a\u53f7", example="13512345678")
    private String phoneNumber;
    @DtoAttribute(value="\u90ae\u7bb1", example="")
    private String email;
    @DtoAttribute(value="\u662f\u5426\u7ba1\u7406\u5458", example="false")
    private Boolean admin;
    @DtoAttribute(value="\u7c7b\u578b", example="INTERNAL")
    private CtpUserSpiUserTypeEnum type = CtpUserSpiUserTypeEnum.INTERNAL;
    @DtoAttribute(value="\u4eba\u5458ID", example="60828711522402304")
    private Long memberId;
    @DtoAttribute(value="\u6240\u5c5e\u673a\u6784ID", example="60828711522402304")
    private Long orgId;
    @DtoAttribute(value="\u6240\u5c5e\u673a\u6784\u540d\u79f0", example="\u5317\u4eac\u81f4\u8fdc")
    private String orgName;
    @DtoAttribute(value="\u6388\u6743\u767b\u5f55\u673a\u6784ID\u96c6\u5408", example="[60828711522402304,60828711522402304]")
    private List<Long> authOrgIdList;
    @DtoAttribute(value="\u662f\u5426\u542f\u7528", example="true")
    private Boolean enabled = true;
    @DtoAttribute(value="\u9996\u9009\u8bed\u8a00", example="zh_CN")
    private String locale;
    @DtoAttribute(value="\u751f\u6548\u65f6\u95f4", example="1604467355352")
    private Date effectiveTime;
    @DtoAttribute(value="\u5931\u6548\u65f6\u95f4", example="1637480629922")
    private Date invalidTime;
    @DtoAttribute(value="\u662f\u5426\u751f\u6548", example="true")
    private Boolean effective;
    @DtoAttribute(value="\u6700\u8fd1\u767b\u5f55\u8bbe\u5907", example="60828711522402304")
    private String lastLoginDevice;
    @DtoAttribute(value="\u6700\u8fd1\u767b\u5f55IP", example="10.0.0.1")
    private String lastLoginIp;
    @DtoAttribute(value="\u6700\u8fd1\u767b\u5f55\u65f6\u95f4", example="1604467355352")
    private Date lastLoginTime;
    @DtoAttribute(value="\u521b\u5efa\u65f6\u95f4", example="1604467355352")
    private Date createTime;
    @DtoAttribute(value="\u4efb\u804cid", example="-1")
    private Long memberPostId = -1L;
    @DtoAttribute(value="\u5404\u7aef\u767b\u5f55\u65f6\u95f4", example="")
    private String clientLoginTime;

    public Boolean getEffective() {
        try {
            Date date = new Date();
            if (this.getEnabled().booleanValue() && !this.getEffectiveTime().after(date) && this.getInvalidTime().after(date)) {
                return true;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        return false;
    }

    public boolean isCredentialsNonExpired() {
        try {
            Date date = new Date();
            return this.getExpiredTime().after(date);
        }
        catch (Exception exception) {
            return false;
        }
    }

    public static CtpUserSpiUserDtoBuilder builder() {
        return new CtpUserSpiUserDtoBuilder();
    }

    public Long getId() {
        return this.id;
    }

    public Long getTenantId() {
        return this.tenantId;
    }

    public String getName() {
        return this.name;
    }

    public String getLoginName() {
        return this.loginName;
    }

    public String getPassword() {
        return this.password;
    }

    public Date getExpiredTime() {
        return this.expiredTime;
    }

    public String getAvatar() {
        return this.avatar;
    }

    public String getPhoneNumber() {
        return this.phoneNumber;
    }

    public String getEmail() {
        return this.email;
    }

    public Boolean getAdmin() {
        return this.admin;
    }

    public CtpUserSpiUserTypeEnum getType() {
        return this.type;
    }

    public Long getMemberId() {
        return this.memberId;
    }

    public Long getOrgId() {
        return this.orgId;
    }

    public String getOrgName() {
        return this.orgName;
    }

    public List<Long> getAuthOrgIdList() {
        return this.authOrgIdList;
    }

    public Boolean getEnabled() {
        return this.enabled;
    }

    public String getLocale() {
        return this.locale;
    }

    public Date getEffectiveTime() {
        return this.effectiveTime;
    }

    public Date getInvalidTime() {
        return this.invalidTime;
    }

    public String getLastLoginDevice() {
        return this.lastLoginDevice;
    }

    public String getLastLoginIp() {
        return this.lastLoginIp;
    }

    public Date getLastLoginTime() {
        return this.lastLoginTime;
    }

    public Date getCreateTime() {
        return this.createTime;
    }

    public Long getMemberPostId() {
        return this.memberPostId;
    }

    public String getClientLoginTime() {
        return this.clientLoginTime;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public void setTenantId(Long tenantId) {
        this.tenantId = tenantId;
    }

    public void setName(String name) {
        this.name = name;
    }

    public void setLoginName(String loginName) {
        this.loginName = loginName;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public void setExpiredTime(Date expiredTime) {
        this.expiredTime = expiredTime;
    }

    public void setAvatar(String avatar) {
        this.avatar = avatar;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public void setAdmin(Boolean admin) {
        this.admin = admin;
    }

    public void setType(CtpUserSpiUserTypeEnum type) {
        this.type = type;
    }

    public void setMemberId(Long memberId) {
        this.memberId = memberId;
    }

    public void setOrgId(Long orgId) {
        this.orgId = orgId;
    }

    public void setOrgName(String orgName) {
        this.orgName = orgName;
    }

    public void setAuthOrgIdList(List<Long> authOrgIdList) {
        this.authOrgIdList = authOrgIdList;
    }

    public void setEnabled(Boolean enabled) {
        this.enabled = enabled;
    }

    public void setLocale(String locale) {
        this.locale = locale;
    }

    public void setEffectiveTime(Date effectiveTime) {
        this.effectiveTime = effectiveTime;
    }

    public void setInvalidTime(Date invalidTime) {
        this.invalidTime = invalidTime;
    }

    public void setEffective(Boolean effective) {
        this.effective = effective;
    }

    public void setLastLoginDevice(String lastLoginDevice) {
        this.lastLoginDevice = lastLoginDevice;
    }

    public void setLastLoginIp(String lastLoginIp) {
        this.lastLoginIp = lastLoginIp;
    }

    public void setLastLoginTime(Date lastLoginTime) {
        this.lastLoginTime = lastLoginTime;
    }

    public void setCreateTime(Date createTime) {
        this.createTime = createTime;
    }

    public void setMemberPostId(Long memberPostId) {
        this.memberPostId = memberPostId;
    }

    public void setClientLoginTime(String clientLoginTime) {
        this.clientLoginTime = clientLoginTime;
    }

    public String toString() {
        return "CtpUserSpiUserDto(id=" + this.getId() + ", tenantId=" + this.getTenantId() + ", name=" + this.getName() + ", loginName=" + this.getLoginName() + ", password=" + this.getPassword() + ", expiredTime=" + this.getExpiredTime() + ", avatar=" + this.getAvatar() + ", phoneNumber=" + this.getPhoneNumber() + ", email=" + this.getEmail() + ", admin=" + this.getAdmin() + ", type=" + (Object)((Object)this.getType()) + ", memberId=" + this.getMemberId() + ", orgId=" + this.getOrgId() + ", orgName=" + this.getOrgName() + ", authOrgIdList=" + this.getAuthOrgIdList() + ", enabled=" + this.getEnabled() + ", locale=" + this.getLocale() + ", effectiveTime=" + this.getEffectiveTime() + ", invalidTime=" + this.getInvalidTime() + ", effective=" + this.getEffective() + ", lastLoginDevice=" + this.getLastLoginDevice() + ", lastLoginIp=" + this.getLastLoginIp() + ", lastLoginTime=" + this.getLastLoginTime() + ", createTime=" + this.getCreateTime() + ", memberPostId=" + this.getMemberPostId() + ", clientLoginTime=" + this.getClientLoginTime() + ")";
    }

    public CtpUserSpiUserDto() {
    }

    public CtpUserSpiUserDto(Long id, Long tenantId, String name, String loginName, String password, Date expiredTime, String avatar, String phoneNumber, String email, Boolean admin, CtpUserSpiUserTypeEnum type, Long memberId, Long orgId, String orgName, List<Long> authOrgIdList, Boolean enabled, String locale, Date effectiveTime, Date invalidTime, Boolean effective, String lastLoginDevice, String lastLoginIp, Date lastLoginTime, Date createTime, Long memberPostId, String clientLoginTime) {
        this.id = id;
        this.tenantId = tenantId;
        this.name = name;
        this.loginName = loginName;
        this.password = password;
        this.expiredTime = expiredTime;
        this.avatar = avatar;
        this.phoneNumber = phoneNumber;
        this.email = email;
        this.admin = admin;
        this.type = type;
        this.memberId = memberId;
        this.orgId = orgId;
        this.orgName = orgName;
        this.authOrgIdList = authOrgIdList;
        this.enabled = enabled;
        this.locale = locale;
        this.effectiveTime = effectiveTime;
        this.invalidTime = invalidTime;
        this.effective = effective;
        this.lastLoginDevice = lastLoginDevice;
        this.lastLoginIp = lastLoginIp;
        this.lastLoginTime = lastLoginTime;
        this.createTime = createTime;
        this.memberPostId = memberPostId;
        this.clientLoginTime = clientLoginTime;
    }

    public static class CtpUserSpiUserDtoBuilder {
        private Long id;
        private Long tenantId;
        private String name;
        private String loginName;
        private String password;
        private Date expiredTime;
        private String avatar;
        private String phoneNumber;
        private String email;
        private Boolean admin;
        private CtpUserSpiUserTypeEnum type;
        private Long memberId;
        private Long orgId;
        private String orgName;
        private List<Long> authOrgIdList;
        private Boolean enabled;
        private String locale;
        private Date effectiveTime;
        private Date invalidTime;
        private Boolean effective;
        private String lastLoginDevice;
        private String lastLoginIp;
        private Date lastLoginTime;
        private Date createTime;
        private Long memberPostId;
        private String clientLoginTime;

        CtpUserSpiUserDtoBuilder() {
        }

        public CtpUserSpiUserDtoBuilder id(Long id) {
            this.id = id;
            return this;
        }

        public CtpUserSpiUserDtoBuilder tenantId(Long tenantId) {
            this.tenantId = tenantId;
            return this;
        }

        public CtpUserSpiUserDtoBuilder name(String name) {
            this.name = name;
            return this;
        }

        public CtpUserSpiUserDtoBuilder loginName(String loginName) {
            this.loginName = loginName;
            return this;
        }

        public CtpUserSpiUserDtoBuilder password(String password) {
            this.password = password;
            return this;
        }

        public CtpUserSpiUserDtoBuilder expiredTime(Date expiredTime) {
            this.expiredTime = expiredTime;
            return this;
        }

        public CtpUserSpiUserDtoBuilder avatar(String avatar) {
            this.avatar = avatar;
            return this;
        }

        public CtpUserSpiUserDtoBuilder phoneNumber(String phoneNumber) {
            this.phoneNumber = phoneNumber;
            return this;
        }

        public CtpUserSpiUserDtoBuilder email(String email) {
            this.email = email;
            return this;
        }

        public CtpUserSpiUserDtoBuilder admin(Boolean admin) {
            this.admin = admin;
            return this;
        }

        public CtpUserSpiUserDtoBuilder type(CtpUserSpiUserTypeEnum type) {
            this.type = type;
            return this;
        }

        public CtpUserSpiUserDtoBuilder memberId(Long memberId) {
            this.memberId = memberId;
            return this;
        }

        public CtpUserSpiUserDtoBuilder orgId(Long orgId) {
            this.orgId = orgId;
            return this;
        }

        public CtpUserSpiUserDtoBuilder orgName(String orgName) {
            this.orgName = orgName;
            return this;
        }

        public CtpUserSpiUserDtoBuilder authOrgIdList(List<Long> authOrgIdList) {
            this.authOrgIdList = authOrgIdList;
            return this;
        }

        public CtpUserSpiUserDtoBuilder enabled(Boolean enabled) {
            this.enabled = enabled;
            return this;
        }

        public CtpUserSpiUserDtoBuilder locale(String locale) {
            this.locale = locale;
            return this;
        }

        public CtpUserSpiUserDtoBuilder effectiveTime(Date effectiveTime) {
            this.effectiveTime = effectiveTime;
            return this;
        }

        public CtpUserSpiUserDtoBuilder invalidTime(Date invalidTime) {
            this.invalidTime = invalidTime;
            return this;
        }

        public CtpUserSpiUserDtoBuilder effective(Boolean effective) {
            this.effective = effective;
            return this;
        }

        public CtpUserSpiUserDtoBuilder lastLoginDevice(String lastLoginDevice) {
            this.lastLoginDevice = lastLoginDevice;
            return this;
        }

        public CtpUserSpiUserDtoBuilder lastLoginIp(String lastLoginIp) {
            this.lastLoginIp = lastLoginIp;
            return this;
        }

        public CtpUserSpiUserDtoBuilder lastLoginTime(Date lastLoginTime) {
            this.lastLoginTime = lastLoginTime;
            return this;
        }

        public CtpUserSpiUserDtoBuilder createTime(Date createTime) {
            this.createTime = createTime;
            return this;
        }

        public CtpUserSpiUserDtoBuilder memberPostId(Long memberPostId) {
            this.memberPostId = memberPostId;
            return this;
        }

        public CtpUserSpiUserDtoBuilder clientLoginTime(String clientLoginTime) {
            this.clientLoginTime = clientLoginTime;
            return this;
        }

        public CtpUserSpiUserDto build() {
            return new CtpUserSpiUserDto(this.id, this.tenantId, this.name, this.loginName, this.password, this.expiredTime, this.avatar, this.phoneNumber, this.email, this.admin, this.type, this.memberId, this.orgId, this.orgName, this.authOrgIdList, this.enabled, this.locale, this.effectiveTime, this.invalidTime, this.effective, this.lastLoginDevice, this.lastLoginIp, this.lastLoginTime, this.createTime, this.memberPostId, this.clientLoginTime);
        }

        public String toString() {
            return "CtpUserSpiUserDto.CtpUserSpiUserDtoBuilder(id=" + this.id + ", tenantId=" + this.tenantId + ", name=" + this.name + ", loginName=" + this.loginName + ", password=" + this.password + ", expiredTime=" + this.expiredTime + ", avatar=" + this.avatar + ", phoneNumber=" + this.phoneNumber + ", email=" + this.email + ", admin=" + this.admin + ", type=" + (Object)((Object)this.type) + ", memberId=" + this.memberId + ", orgId=" + this.orgId + ", orgName=" + this.orgName + ", authOrgIdList=" + this.authOrgIdList + ", enabled=" + this.enabled + ", locale=" + this.locale + ", effectiveTime=" + this.effectiveTime + ", invalidTime=" + this.invalidTime + ", effective=" + this.effective + ", lastLoginDevice=" + this.lastLoginDevice + ", lastLoginIp=" + this.lastLoginIp + ", lastLoginTime=" + this.lastLoginTime + ", createTime=" + this.createTime + ", memberPostId=" + this.memberPostId + ", clientLoginTime=" + this.clientLoginTime + ")";
        }
    }
}

