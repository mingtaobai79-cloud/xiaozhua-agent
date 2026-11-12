/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.dto.activity.BpmActivityBaseDto
 *  com.seeyon.bpm.enums.AppointStepBackStyleEnum
 */
package com.seeyon.bpm.dto.message.event;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.dto.activity.BpmActivityBaseDto;
import com.seeyon.bpm.dto.message.event.BpmBaseEvent;
import com.seeyon.bpm.enums.AppointStepBackStyleEnum;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@DtoInfo(value="bpm\u56de\u9000\u4e8b\u4ef6\u89e6\u53d1\u5185\u5bb9")
public class BpmStepbackEvent
extends BpmBaseEvent {
    @DtoAttribute(value="\u4e8b\u9879ID", example="")
    private Long affairId;
    @DtoAttribute(value="\u64cd\u4f5c\u65f6\u95f4", example="")
    private Date actionTime;
    @DtoAttribute(value="\u662f\u5426\u56de\u9000\u5230\u53d1\u8d77\u8282\u70b9", example="60828711522402306")
    private Boolean toStart;
    @DtoAttribute(value="\u5f53\u524d\u8282\u70b9ID", example="60828711522402306")
    private Long currentActivityId;
    @DtoAttribute(value="\u5f53\u524d\u8282\u70b9\u540d\u79f0", example="\u53d1\u8d77\u8005")
    private String currentActivityName;
    @DtoAttribute(value="\u4e8b\u4ef6\u540d\u79f0", example="")
    private String eventName = "\u6d41\u7a0b\u56de\u9000\u6d88\u606f";
    @DtoAttribute(value="\u610f\u89c1\u4fe1\u606f")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="\u56de\u9000\u65b9\u5f0f")
    private AppointStepBackStyleEnum stepBackStyle = AppointStepBackStyleEnum.NODE_GO_BACK;
    @DtoAttribute(value="\u56de\u9000\u5230\u7684\u8282\u70b9id\u548c\u8282\u70b9\u540d\u79f0")
    private List<BpmActivityBaseDto> stepBackToActivitys = new ArrayList<BpmActivityBaseDto>();
    @DtoAttribute(value="\u56de\u9000\u539f\u8282\u70b9\u7684\u7c7b\u578b")
    private String sourceNodeType;
    @DtoAttribute(value="\u8868\u5355\u6743\u9650id", example="123")
    private Long formOperationId;

    public Long getAffairId() {
        return this.affairId;
    }

    @Override
    public Date getActionTime() {
        return this.actionTime;
    }

    public Boolean getToStart() {
        return this.toStart;
    }

    @Override
    public Long getCurrentActivityId() {
        return this.currentActivityId;
    }

    @Override
    public String getCurrentActivityName() {
        return this.currentActivityName;
    }

    public String getEventName() {
        return this.eventName;
    }

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public AppointStepBackStyleEnum getStepBackStyle() {
        return this.stepBackStyle;
    }

    public List<BpmActivityBaseDto> getStepBackToActivitys() {
        return this.stepBackToActivitys;
    }

    public String getSourceNodeType() {
        return this.sourceNodeType;
    }

    public Long getFormOperationId() {
        return this.formOperationId;
    }

    public void setAffairId(Long affairId) {
        this.affairId = affairId;
    }

    @Override
    public void setActionTime(Date actionTime) {
        this.actionTime = actionTime;
    }

    public void setToStart(Boolean toStart) {
        this.toStart = toStart;
    }

    @Override
    public void setCurrentActivityId(Long currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    @Override
    public void setCurrentActivityName(String currentActivityName) {
        this.currentActivityName = currentActivityName;
    }

    public void setEventName(String eventName) {
        this.eventName = eventName;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }

    public void setStepBackStyle(AppointStepBackStyleEnum stepBackStyle) {
        this.stepBackStyle = stepBackStyle;
    }

    public void setStepBackToActivitys(List<BpmActivityBaseDto> stepBackToActivitys) {
        this.stepBackToActivitys = stepBackToActivitys;
    }

    public void setSourceNodeType(String sourceNodeType) {
        this.sourceNodeType = sourceNodeType;
    }

    public void setFormOperationId(Long formOperationId) {
        this.formOperationId = formOperationId;
    }
}
