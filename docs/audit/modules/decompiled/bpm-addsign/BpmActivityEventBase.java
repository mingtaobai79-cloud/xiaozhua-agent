/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.dto.message.event.BpmBaseEvent
 *  com.seeyon.bpm.enums.BpmActivityTypeEnum
 */
package com.seeyon.bpm.dto.message.event;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.dto.message.event.BpmBaseEvent;
import com.seeyon.bpm.enums.BpmActivityTypeEnum;
import java.util.Map;

@DtoInfo(value="节点事件基类")
public class BpmActivityEventBase
extends BpmBaseEvent {
    @DtoAttribute(value="当前节点ID", example="60828711522402306")
    private Long currentActivityId;
    @DtoAttribute(value="当前节点名称", example="发起者")
    private String currentActivityName;
    @DtoAttribute(value="当前节点类型", example="BPM_HUMEN_ACTIVITY")
    private BpmActivityTypeEnum currentActivityType;
    @DtoAttribute(value="参数数据", example="")
    private Map<String, Object> parameters;
    @DtoAttribute(value="消息名称", example="", hidden=true)
    private String eventName;
    @DtoAttribute(value="事件名称", example="")
    private String eventTitle;
    @DtoAttribute(value="意见信息")
    private BpmCommentDto commentDto;

    public Long getCurrentActivityId() {
        return this.currentActivityId;
    }

    public String getCurrentActivityName() {
        return this.currentActivityName;
    }

    public BpmActivityTypeEnum getCurrentActivityType() {
        return this.currentActivityType;
    }

    public Map<String, Object> getParameters() {
        return this.parameters;
    }

    public String getEventName() {
        return this.eventName;
    }

    public String getEventTitle() {
        return this.eventTitle;
    }

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public void setCurrentActivityId(Long currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    public void setCurrentActivityName(String currentActivityName) {
        this.currentActivityName = currentActivityName;
    }

    public void setCurrentActivityType(BpmActivityTypeEnum currentActivityType) {
        this.currentActivityType = currentActivityType;
    }

    public void setParameters(Map<String, Object> parameters) {
        this.parameters = parameters;
    }

    public void setEventName(String eventName) {
        this.eventName = eventName;
    }

    public void setEventTitle(String eventTitle) {
        this.eventTitle = eventTitle;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }
}
