/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.dto.activity.BpmActivityBaseDto
 *  com.seeyon.bpm.dto.message.event.BpmBaseEvent
 *  com.seeyon.bpm.enums.ActivityStateEnum
 *  com.seeyon.bpm.enums.WorkItemActionStateEnum
 *  com.seeyon.bpm.enums.WorkItemStateEnum
 */
package com.seeyon.bpm.dto.message.event;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.dto.activity.BpmActivityBaseDto;
import com.seeyon.bpm.dto.message.event.BpmBaseEvent;
import com.seeyon.bpm.enums.ActivityStateEnum;
import com.seeyon.bpm.enums.WorkItemActionStateEnum;
import com.seeyon.bpm.enums.WorkItemStateEnum;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@DtoInfo(value="bpm事项完成消息内容")
public class BpmSubmitEvent
extends BpmBaseEvent {
    private static final long serialVersionUID = 1322594026182790423L;
    @DtoAttribute(value="当前节点ID", example="60828711522402306")
    private Long currentActivityId;
    @DtoAttribute(value="当前节点名称", example="发起者")
    private String currentActivityName;
    @DtoAttribute(value="事项id", example="")
    private Long affairId;
    @DtoAttribute(value="事项完成时间", example="")
    private Date affairFinishTime;
    @DtoAttribute(value="表单操作权限id", example="123")
    private Long formOperationId;
    @DtoAttribute(value="节点状态", example="123")
    private ActivityStateEnum activityState = ActivityStateEnum.NORMAL;
    @DtoAttribute(value="事件名称", example="")
    private String eventName = "事项结束消息";
    @DtoAttribute(value="提交前事项状态")
    private WorkItemStateEnum beforeWorkItemState = WorkItemStateEnum.NONE;
    @DtoAttribute(value="提交前事项子状态")
    private WorkItemActionStateEnum beforeWorkItemSubState = WorkItemActionStateEnum.NONE;
    @DtoAttribute(value="意见信息")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="提交到的节点id和名称")
    private List<BpmActivityBaseDto> toActivity = new ArrayList<BpmActivityBaseDto>();
    @DtoAttribute(value="是否为合并处理提交")
    private boolean isMergeSubmit;
    @DtoAttribute(value="处理方式", description="NORMAL（常规处理提交）；OVERDUE（超期自动跳过）；SKIP（督办跳过）；REPEAT（重复跳过、合并处理）；SUPERVISOR（无人转督办人选择）；INTERFACE_SKIP（接口跳过）；AUTO_SKIP（自动跳过）；POST_APPROVAL_SKIP（后置审批跳过）")
    private String finishType = "NORMAL";

    public Long getCurrentActivityId() {
        return this.currentActivityId;
    }

    public String getCurrentActivityName() {
        return this.currentActivityName;
    }

    public Long getAffairId() {
        return this.affairId;
    }

    public Date getAffairFinishTime() {
        return this.affairFinishTime;
    }

    public Long getFormOperationId() {
        return this.formOperationId;
    }

    public ActivityStateEnum getActivityState() {
        return this.activityState;
    }

    public String getEventName() {
        return this.eventName;
    }

    public WorkItemStateEnum getBeforeWorkItemState() {
        return this.beforeWorkItemState;
    }

    public WorkItemActionStateEnum getBeforeWorkItemSubState() {
        return this.beforeWorkItemSubState;
    }

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public List<BpmActivityBaseDto> getToActivity() {
        return this.toActivity;
    }

    public boolean isMergeSubmit() {
        return this.isMergeSubmit;
    }

    public String getFinishType() {
        return this.finishType;
    }

    public void setCurrentActivityId(Long currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    public void setCurrentActivityName(String currentActivityName) {
        this.currentActivityName = currentActivityName;
    }

    public void setAffairId(Long affairId) {
        this.affairId = affairId;
    }

    public void setAffairFinishTime(Date affairFinishTime) {
        this.affairFinishTime = affairFinishTime;
    }

    public void setFormOperationId(Long formOperationId) {
        this.formOperationId = formOperationId;
    }

    public void setActivityState(ActivityStateEnum activityState) {
        this.activityState = activityState;
    }

    public void setEventName(String eventName) {
        this.eventName = eventName;
    }

    public void setBeforeWorkItemState(WorkItemStateEnum beforeWorkItemState) {
        this.beforeWorkItemState = beforeWorkItemState;
    }

    public void setBeforeWorkItemSubState(WorkItemActionStateEnum beforeWorkItemSubState) {
        this.beforeWorkItemSubState = beforeWorkItemSubState;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }

    public void setToActivity(List<BpmActivityBaseDto> toActivity) {
        this.toActivity = toActivity;
    }

    public void setMergeSubmit(boolean isMergeSubmit) {
        this.isMergeSubmit = isMergeSubmit;
    }

    public void setFinishType(String finishType) {
        this.finishType = finishType;
    }
}
