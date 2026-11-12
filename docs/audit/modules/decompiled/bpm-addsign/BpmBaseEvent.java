/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.util.StringUtils
 *  com.seeyon.bpm.dto.message.BpmMqData
 *  com.seeyon.bpm.enums.BpmActivityTypeEnum
 *  com.seeyon.bpm.enums.CaseApprovalState
 *  com.seeyon.bpm.enums.CaseStateEnum
 *  com.seeyon.bpm.enums.CaseTypeEnum
 *  com.seeyon.bpm.enums.ChangeTypeEnum
 */
package com.seeyon.bpm.dto.message.event;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.bpm.dto.message.BpmMqData;
import com.seeyon.bpm.enums.BpmActivityTypeEnum;
import com.seeyon.bpm.enums.CaseApprovalState;
import com.seeyon.bpm.enums.CaseStateEnum;
import com.seeyon.bpm.enums.CaseTypeEnum;
import com.seeyon.bpm.enums.ChangeTypeEnum;
import java.util.Date;

@DtoInfo(value="bpm事件触发消息")
public class BpmBaseEvent
extends BpmMqData {
    private static final long serialVersionUID = 9129090643870175871L;
    @DtoAttribute(value="流程实例ID", example="60828711522402304")
    private Long caseId;
    @DtoAttribute(value="流程实例名称", example="60828711522402304")
    private String subject;
    @DtoAttribute(value="流程实例国际化名称", example="")
    private String caseI18nSubject;
    @DtoAttribute(value="所属应用名", example="app-approval")
    private String appName;
    @DtoAttribute(value="操作时间", example="")
    private Date actionTime = new Date();
    @DtoAttribute(value="流程发起人id", example="123", relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization", customs={@Custom(name="openApiCustom", properties={@CustomAttribute(name="escapeAttributeNameAlias", value="startUserCode")})})
    private Long startUserId;
    @DtoAttribute(value="当前用户Id", example="60828711522402304", relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization", customs={@Custom(name="openApiCustom", properties={@CustomAttribute(name="escapeAttributeNameAlias", value="currentUserCode")})})
    private Long currentUserId;
    @DtoAttribute(value="流程状态", example="STATE_RUNNING")
    private CaseStateEnum caseState = CaseStateEnum.NONE;
    @DtoAttribute(value="审批状态", example="AGREE")
    private CaseApprovalState approvalState = CaseApprovalState.NONE;
    @DtoAttribute(value="根实体fullName", example="")
    private String rootEntityFullName;
    @DtoAttribute(value="应用主数据ID", example="9129090643870175871")
    @Deprecated
    private Long formRecordId;
    @DtoAttribute(value="表单数据唯一标记", example="9129090643870175871")
    private String formRecordCode;
    @DtoAttribute(value="当前节点ID", example="")
    private Long currentActivityId;
    @DtoAttribute(value="当前节点Code", example="")
    private String currentActivityCode;
    @DtoAttribute(value="当前节点名称", example="")
    private String currentActivityName;
    @DtoAttribute(value="当前节点类型", example="BPM_HUMEN_ACTIVITY")
    private BpmActivityTypeEnum currentActivityType;
    @DtoAttribute(value="当前节点分组id。默认值为0,表示没有分组", example="123")
    private Long currentActivityGroupId;
    @DtoAttribute(value="当前节点是加签，知会，会签出来", example="123")
    private ChangeTypeEnum currentActivityChangeType;
    @DtoAttribute(value="模板编码", example="")
    private String templateCode;
    @DtoAttribute(value="模板id", example="")
    private Long templateId;
    @DtoAttribute(value="模板guid", example="")
    private Long templateGuid;
    @DtoAttribute(value="流程类型，主流程还是子流程", example="0")
    private CaseTypeEnum processType = CaseTypeEnum.MAIN_PROCESS;
    @DtoAttribute(value="是否来源于督办", example="false")
    private Boolean isSupervise = Boolean.FALSE;

    public void setFormRecordCode(String formRecordCode) {
        this.formRecordCode = formRecordCode;
        this.formRecordId = StringUtils.isNumber((CharSequence)formRecordCode) ? Long.valueOf(formRecordCode) : null;
    }

    public Long getCaseId() {
        return this.caseId;
    }

    public String getSubject() {
        return this.subject;
    }

    public String getCaseI18nSubject() {
        return this.caseI18nSubject;
    }

    public String getAppName() {
        return this.appName;
    }

    public Date getActionTime() {
        return this.actionTime;
    }

    public Long getStartUserId() {
        return this.startUserId;
    }

    public Long getCurrentUserId() {
        return this.currentUserId;
    }

    public CaseStateEnum getCaseState() {
        return this.caseState;
    }

    public CaseApprovalState getApprovalState() {
        return this.approvalState;
    }

    public String getRootEntityFullName() {
        return this.rootEntityFullName;
    }

    @Deprecated
    public Long getFormRecordId() {
        return this.formRecordId;
    }

    public String getFormRecordCode() {
        return this.formRecordCode;
    }

    public Long getCurrentActivityId() {
        return this.currentActivityId;
    }

    public String getCurrentActivityCode() {
        return this.currentActivityCode;
    }

    public String getCurrentActivityName() {
        return this.currentActivityName;
    }

    public BpmActivityTypeEnum getCurrentActivityType() {
        return this.currentActivityType;
    }

    public Long getCurrentActivityGroupId() {
        return this.currentActivityGroupId;
    }

    public ChangeTypeEnum getCurrentActivityChangeType() {
        return this.currentActivityChangeType;
    }

    public String getTemplateCode() {
        return this.templateCode;
    }

    public Long getTemplateId() {
        return this.templateId;
    }

    public Long getTemplateGuid() {
        return this.templateGuid;
    }

    public CaseTypeEnum getProcessType() {
        return this.processType;
    }

    public Boolean getIsSupervise() {
        return this.isSupervise;
    }

    public void setCaseId(Long caseId) {
        this.caseId = caseId;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public void setCaseI18nSubject(String caseI18nSubject) {
        this.caseI18nSubject = caseI18nSubject;
    }

    public void setAppName(String appName) {
        this.appName = appName;
    }

    public void setActionTime(Date actionTime) {
        this.actionTime = actionTime;
    }

    public void setStartUserId(Long startUserId) {
        this.startUserId = startUserId;
    }

    public void setCurrentUserId(Long currentUserId) {
        this.currentUserId = currentUserId;
    }

    public void setCaseState(CaseStateEnum caseState) {
        this.caseState = caseState;
    }

    public void setApprovalState(CaseApprovalState approvalState) {
        this.approvalState = approvalState;
    }

    public void setRootEntityFullName(String rootEntityFullName) {
        this.rootEntityFullName = rootEntityFullName;
    }

    @Deprecated
    public void setFormRecordId(Long formRecordId) {
        this.formRecordId = formRecordId;
    }

    public void setCurrentActivityId(Long currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    public void setCurrentActivityCode(String currentActivityCode) {
        this.currentActivityCode = currentActivityCode;
    }

    public void setCurrentActivityName(String currentActivityName) {
        this.currentActivityName = currentActivityName;
    }

    public void setCurrentActivityType(BpmActivityTypeEnum currentActivityType) {
        this.currentActivityType = currentActivityType;
    }

    public void setCurrentActivityGroupId(Long currentActivityGroupId) {
        this.currentActivityGroupId = currentActivityGroupId;
    }

    public void setCurrentActivityChangeType(ChangeTypeEnum currentActivityChangeType) {
        this.currentActivityChangeType = currentActivityChangeType;
    }

    public void setTemplateCode(String templateCode) {
        this.templateCode = templateCode;
    }

    public void setTemplateId(Long templateId) {
        this.templateId = templateId;
    }

    public void setTemplateGuid(Long templateGuid) {
        this.templateGuid = templateGuid;
    }

    public void setProcessType(CaseTypeEnum processType) {
        this.processType = processType;
    }

    public void setIsSupervise(Boolean isSupervise) {
        this.isSupervise = isSupervise;
    }
}
