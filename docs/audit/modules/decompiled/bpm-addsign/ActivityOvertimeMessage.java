/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.formtemplate.ActivityOvertimeSetDto
 *  com.seeyon.bpm.dto.message.overtime.ProcessOvertimeMessage
 */
package com.seeyon.bpm.dto.message.overtime;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.formtemplate.ActivityOvertimeSetDto;
import com.seeyon.bpm.dto.message.overtime.ProcessOvertimeMessage;

@DtoInfo(value="节点超期消息")
public class ActivityOvertimeMessage
extends ProcessOvertimeMessage {
    @DtoAttribute(value="节点Id", example="1232332")
    private Long activityId;
    @DtoAttribute(value="事项Id", example="1232332")
    private Long workItermId;
    @DtoAttribute(value="是否是高级设置的消息", example="false")
    private Boolean advanceMessage;
    @DtoAttribute(value="节点超期设置", example="")
    private ActivityOvertimeSetDto activityOvertimeSet;

    public Long getActivityId() {
        return this.activityId;
    }

    public Long getWorkItermId() {
        return this.workItermId;
    }

    public Boolean getAdvanceMessage() {
        return this.advanceMessage;
    }

    public ActivityOvertimeSetDto getActivityOvertimeSet() {
        return this.activityOvertimeSet;
    }

    public void setActivityId(Long activityId) {
        this.activityId = activityId;
    }

    public void setWorkItermId(Long workItermId) {
        this.workItermId = workItermId;
    }

    public void setAdvanceMessage(Boolean advanceMessage) {
        this.advanceMessage = advanceMessage;
    }

    public void setActivityOvertimeSet(ActivityOvertimeSetDto activityOvertimeSet) {
        this.activityOvertimeSet = activityOvertimeSet;
    }
}
