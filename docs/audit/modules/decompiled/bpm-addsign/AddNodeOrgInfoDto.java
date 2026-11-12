/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import javax.validation.constraints.NotNull;

@DtoInfo(value="\u52a0\u7b7e\u6216\u8005\u66ff\u6362\u7684\u4eba\u5458\u4fe1\u606f")
public class AddNodeOrgInfoDto
extends BaseDto {
    @DtoAttribute(value="\u52a0\u7b7e\u7684\u8282\u70b9id\u3002\u53ea\u4f1a,\u52a0\u7b7e\u5230\u8282\u70b9\u5185\u4e0d\u4f20\u8282\u70b9id\uff0c\u66ff\u6362\u65f6\u9700\u8981\u4f20\u5165\u9700\u8981\u66ff\u6362\u7684\u8282\u70b9id", example="")
    private String activityId;
    @DtoAttribute(value="\u52a0\u7b7e\u7684\u8282\u70b9\u540d\u79f0\u3002\u5408\u5e76\u4e3a\u4e00\u4e2a\u8282\u70b9\u65f6\uff0c\u8be5\u5c5e\u6027\u4e0d\u80fd\u4e3a\u7a7a\uff0c\u5426\u5219\u9ed8\u8ba4\u53d6\u7b2c\u4e00\u4e2a\u53c2\u4e0e\u8005\u7684\u540d\u79f0\u4f5c\u4e3a\u8282\u70b9\u540d\u79f0", example="")
    private String activityName;
    @DtoAttribute(value="\u9009\u4eba\u754c\u9762\u8fd4\u56de\u7684\u52a0\u7b7e\u7684\u7ec4\u7ec7\u6a21\u578b\u4fe1\u606f", example="")
    @NotNull
    private String orgInfo;

    public AddNodeOrgInfoDto(String activityId, String orgInfo) {
        this.activityId = activityId;
        this.orgInfo = orgInfo;
    }

    public AddNodeOrgInfoDto() {
    }

    public String getActivityId() {
        return this.activityId;
    }

    public String getActivityName() {
        return this.activityName;
    }

    public String getOrgInfo() {
        return this.orgInfo;
    }

    public void setActivityId(String activityId) {
        this.activityId = activityId;
    }

    public void setActivityName(String activityName) {
        this.activityName = activityName;
    }

    public void setOrgInfo(String orgInfo) {
        this.orgInfo = orgInfo;
    }
}
