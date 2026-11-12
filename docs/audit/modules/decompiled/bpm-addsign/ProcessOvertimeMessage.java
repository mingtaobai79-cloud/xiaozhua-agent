/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.OvertimeSettingDto
 */
package com.seeyon.bpm.dto.message.overtime;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.OvertimeSettingDto;
import java.util.Date;

@DtoInfo(value="流程超期消息")
public class ProcessOvertimeMessage
extends BaseDto {
    @DtoAttribute(value="单位Id", example="1232332")
    private Long accountId;
    @DtoAttribute(value="流程Id", example="1232332")
    private Long processId;
    @DtoAttribute(value="模板id", example="123")
    private Long templateId;
    @DtoAttribute(value="所属应用", example="app-approval")
    private String appName;
    @DtoAttribute(value="表单应用id", example="123")
    private Long formAppId;
    @DtoAttribute(value="超期设置", example="")
    private OvertimeSettingDto setting;
    @DtoAttribute(value="消息穿透url", example="")
    private String url;
    @DtoAttribute(value="计算后得出的具体的超期期限", example="")
    private Date deadline;
    @DtoAttribute(value="是否是超期后", example="")
    private boolean afterOvertime = false;

    public Long getAccountId() {
        return this.accountId;
    }

    public Long getProcessId() {
        return this.processId;
    }

    public Long getTemplateId() {
        return this.templateId;
    }

    public String getAppName() {
        return this.appName;
    }

    public Long getFormAppId() {
        return this.formAppId;
    }

    public OvertimeSettingDto getSetting() {
        return this.setting;
    }

    public String getUrl() {
        return this.url;
    }

    public Date getDeadline() {
        return this.deadline;
    }

    public boolean isAfterOvertime() {
        return this.afterOvertime;
    }

    public void setAccountId(Long accountId) {
        this.accountId = accountId;
    }

    public void setProcessId(Long processId) {
        this.processId = processId;
    }

    public void setTemplateId(Long templateId) {
        this.templateId = templateId;
    }

    public void setAppName(String appName) {
        this.appName = appName;
    }

    public void setFormAppId(Long formAppId) {
        this.formAppId = formAppId;
    }

    public void setSetting(OvertimeSettingDto setting) {
        this.setting = setting;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public void setDeadline(Date deadline) {
        this.deadline = deadline;
    }

    public void setAfterOvertime(boolean afterOvertime) {
        this.afterOvertime = afterOvertime;
    }
}
