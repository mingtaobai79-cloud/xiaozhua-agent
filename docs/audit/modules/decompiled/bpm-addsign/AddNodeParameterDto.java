/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.AddNodeOrgInfoDto
 *  com.seeyon.bpm.enums.BeforeExpiredEnum
 *  com.seeyon.bpm.enums.DealTermTypeEnum
 *  com.seeyon.bpm.enums.FlowTypeEnum
 *  com.seeyon.bpm.enums.ProcessExecuteEnum
 *  com.seeyon.bpm.enums.ProcessTermEnum
 *  com.seeyon.bpm.enums.SubProcessExecuteModeEnum
 *  com.seeyon.bpm.enums.TimeTypeEnum
 *  javax.validation.constraints.NotEmpty
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.AddNodeOrgInfoDto;
import com.seeyon.bpm.enums.BeforeExpiredEnum;
import com.seeyon.bpm.enums.DealTermTypeEnum;
import com.seeyon.bpm.enums.FlowTypeEnum;
import com.seeyon.bpm.enums.ProcessExecuteEnum;
import com.seeyon.bpm.enums.ProcessTermEnum;
import com.seeyon.bpm.enums.SubProcessExecuteModeEnum;
import com.seeyon.bpm.enums.TimeTypeEnum;
import java.util.List;
import javax.validation.constraints.NotEmpty;

@DtoInfo(value="\u52a0\u7b7e\u754c\u9762\u9009\u62e9\u7684\u53c2\u6570")
public class AddNodeParameterDto
extends BaseDto {
    @NotEmpty
    @DtoAttribute(value="\u9009\u4eba\u754c\u9762\u8fd4\u56de\u7684\u52a0\u7b7e\u7684\u7ec4\u7ec7\u6a21\u578b\u4fe1\u606f\u548c\u8282\u70b9\u4fe1\u606f", example="\"[{'activityId':'123456', 'orgInfo':'1234567890'}]\"")
    private List<AddNodeOrgInfoDto> nodeIdAndSelectPeoples;
    @DtoAttribute(value="\u52a0\u7b7e\u6a21\u5f0f,\u6b64\u5904\u4ec5\u53ef\u4f7f\u7528 SERIAL\uff1a\u52a0\u7b7e\u5230\u8282\u70b9\u540e\uff1bFRONT\uff1a\u52a0\u7b7e\u5230\u8282\u70b9\u524d\uff1bCURRENT_BRANCH\uff1a\u52a0\u7b7e\u5230\u65c1\u652f\uff1bCURRENT_PARALLEL\uff1a\u4e0e\u5f53\u524d\u8282\u70b9\u5e76\u53d1", example="")
    private FlowTypeEnum flowTypeEnum;
    @DtoAttribute(value="\u6267\u884c\u6a21\u5f0f \u5168\u4f53\u5e76\u53d1 \u7ade\u4e89", example="ALL_PARALLEL")
    private ProcessExecuteEnum processExecuteEnum;
    @DtoAttribute(value="\u591a\u4e2a\u8282\u70b9\u6267\u884c\u6a21\u5f0f  \u4e32\u53d1 \u5e76\u53d1", example="SERIAL")
    private SubProcessExecuteModeEnum nodeExecuteEnum;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650ID", example="")
    private String policyId;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650\u540d\u79f0", example="")
    private String policyName;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650\u7c7b\u578bCode", example="")
    private Integer nodePermType;
    @DtoAttribute(value="\u8282\u70b9\u671f\u9650", example="NO_SETTING")
    private ProcessTermEnum processTerm = ProcessTermEnum.NO;
    @DtoAttribute(value="\u8be5\u6a21\u677f\u7684\u53c2\u6570code\uff0c\u5f53\u8282\u70b9\u671f\u9650\u9009\u62e9\u7684\u662f\u8282\u70b9\u53c2\u6570\u7684\u65f6\u5019\u6709\u6548\uff0c\u5e76\u4e14\u53ea\u80fd\u9009\u62e9\u65e5\u671f\u65f6\u95f4\u7c7b\u578b", example="123456789")
    private String parameterCode;
    @DtoAttribute(value="\u8be5\u6a21\u677f\u7684\u53c2\u6570\u540d\u79f0\uff0c\u548c\u53c2\u6570ID\u5bf9\u5e94\uff0c\u5f53\u8282\u70b9\u671f\u9650\u9009\u62e9\u7684\u662f\u8282\u70b9\u53c2\u6570\u7684\u65f6\u5019\u6709\u6548", example="\u62a5\u9500\u65f6\u95f4")
    private String parameterName;
    @DtoAttribute(value="\u81ea\u5b9a\u4e49\u65f6\u95f4\u6570\u5b57\uff0c\u5f53\u8282\u70b9\u671f\u9650\u9009\u62e9\u7684\u662f\u81ea\u5b9a\u4e49\u65f6\u95f4\u8be5\u53c2\u6570\u624d\u6709\u6548", example="2")
    private Integer customTime;
    @DtoAttribute(value="\u81ea\u5b9a\u4e49\u65f6\u95f4\u7c7b\u578b\uff0c\u53ea\u6709\u8282\u70b9\u671f\u9650\u9009\u62e9\u7684\u662f\u81ea\u5b9a\u4e49\u65f6\u95f4\u8be5\u53c2\u6570\u624d\u6709\u6548", example="HOUR")
    private TimeTypeEnum customTimeType;
    @DtoAttribute(value="\u8282\u70b9\u5230\u671f\u524d\u63d0\u9192\u65f6\u95f4\uff0c\u53ea\u6709\u8282\u70b9\u5230\u671f\u524d\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="1")
    private Integer beforeExpiredTime;
    @DtoAttribute(value="\u8282\u70b9\u5230\u671f\u524d\u63d0\u9192\u65f6\u95f4\u7c7b\u578b\uff0c\u53ea\u662f\u8282\u70b9\u5230\u671f\u524d\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="HOUR")
    private TimeTypeEnum beforeExpiredTimeType;
    @DtoAttribute(value="\u8282\u70b9\u5230\u671f\u524d\u64cd\u4f5c", example="NO_OPERATION")
    private BeforeExpiredEnum beforeExpired = BeforeExpiredEnum.NO_OPERATION;
    @DtoAttribute(value="\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c", example="NO_OPERATION")
    private DealTermTypeEnum afterExpired = DealTermTypeEnum.NO;
    @DtoAttribute(value="\u5230\u671f\u91cd\u590d\u63d0\u9192\u65f6\u95f4\uff0c\u53ea\u6709\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192-\u91cd\u590d\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="2")
    private Integer repealAlertTime;
    @DtoAttribute(value="\u5230\u671f\u91cd\u590d\u63d0\u9192\u65f6\u95f4\u7c7b\u578b\uff0c\u53ea\u6709\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192-\u91cd\u590d\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="HOUR")
    private TimeTypeEnum repealAlertTimeType;
    @DtoAttribute(value="\u6d88\u606f\u63d0\u9192\u63d0\u9192\u5bf9\u8c61", example="")
    private String messageRemindUser;
    @DtoAttribute(value="\u6d88\u606f\u91cd\u590d\u63d0\u9192\u63d0\u9192\u5bf9\u8c61", example="")
    private String messageReRemindUser;
    @DtoAttribute(value="\u8d85\u671f\u540e\u8f6c\u6307\u5b9a\u4eba\u9009\u62e9\u7684\u4eba\u5458\u4fe1\u606f", example="")
    private String dealTermUser;
    @DtoAttribute(value="\u52a0\u7b7e\u4e0e\u6211\u5408\u5e76\uff0c\u5408\u5e76\u5230\u539f\u8282\u70b9\uff0ctrue \u8868\u793a\u7acb\u5373\u6536\u5230  false\u4e3a\u5426", example="true")
    private Boolean receiveImmediate = false;
    @DtoAttribute(value="\u8868\u5355\u6743\u9650ID", example="")
    private String formOperationId;
    @DtoAttribute(value="\u662f\u5426\u53ea\u8bfb:true\u53ea\u8bfb,false\u7f16\u8f91", example="false")
    private Boolean readOnly = false;
    @DtoAttribute(value="\u5230\u671f\u91cd\u590d\u63d0\u9192\u6b21\u6570\uff0c\u53ea\u6709\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192-\u91cd\u590d\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="1")
    private Integer repeatCount;
    @DtoAttribute(value="\u52a0\u7b7e\u56de\u5230\u6211")
    private Boolean addNodeToMe = false;
    @DtoAttribute(value="\u52a0\u7b7e\u5728\u6211\u540e\u9762\u7acb\u5373\u6536\u5230\uff0c\u5f62\u6210\u72ec\u7acb\u8282\u70b9  true \u8868\u793a\u7acb\u5373\u6536\u5230  false\u4e3a\u5426", example="true")
    private Boolean addNodeImmediate = false;

    public List<AddNodeOrgInfoDto> getNodeIdAndSelectPeoples() {
        return this.nodeIdAndSelectPeoples;
    }

    public FlowTypeEnum getFlowTypeEnum() {
        return this.flowTypeEnum;
    }

    public ProcessExecuteEnum getProcessExecuteEnum() {
        return this.processExecuteEnum;
    }

    public SubProcessExecuteModeEnum getNodeExecuteEnum() {
        return this.nodeExecuteEnum;
    }

    public String getPolicyId() {
        return this.policyId;
    }

    public String getPolicyName() {
        return this.policyName;
    }

    public Integer getNodePermType() {
        return this.nodePermType;
    }

    public ProcessTermEnum getProcessTerm() {
        return this.processTerm;
    }

    public String getParameterCode() {
        return this.parameterCode;
    }

    public String getParameterName() {
        return this.parameterName;
    }

    public Integer getCustomTime() {
        return this.customTime;
    }

    public TimeTypeEnum getCustomTimeType() {
        return this.customTimeType;
    }

    public Integer getBeforeExpiredTime() {
        return this.beforeExpiredTime;
    }

    public TimeTypeEnum getBeforeExpiredTimeType() {
        return this.beforeExpiredTimeType;
    }

    public BeforeExpiredEnum getBeforeExpired() {
        return this.beforeExpired;
    }

    public DealTermTypeEnum getAfterExpired() {
        return this.afterExpired;
    }

    public Integer getRepealAlertTime() {
        return this.repealAlertTime;
    }

    public TimeTypeEnum getRepealAlertTimeType() {
        return this.repealAlertTimeType;
    }

    public String getMessageRemindUser() {
        return this.messageRemindUser;
    }

    public String getMessageReRemindUser() {
        return this.messageReRemindUser;
    }

    public String getDealTermUser() {
        return this.dealTermUser;
    }

    public Boolean getReceiveImmediate() {
        return this.receiveImmediate;
    }

    public String getFormOperationId() {
        return this.formOperationId;
    }

    public Boolean getReadOnly() {
        return this.readOnly;
    }

    public Integer getRepeatCount() {
        return this.repeatCount;
    }

    public Boolean getAddNodeToMe() {
        return this.addNodeToMe;
    }

    public Boolean getAddNodeImmediate() {
        return this.addNodeImmediate;
    }

    public void setNodeIdAndSelectPeoples(List<AddNodeOrgInfoDto> nodeIdAndSelectPeoples) {
        this.nodeIdAndSelectPeoples = nodeIdAndSelectPeoples;
    }

    public void setFlowTypeEnum(FlowTypeEnum flowTypeEnum) {
        this.flowTypeEnum = flowTypeEnum;
    }

    public void setProcessExecuteEnum(ProcessExecuteEnum processExecuteEnum) {
        this.processExecuteEnum = processExecuteEnum;
    }

    public void setNodeExecuteEnum(SubProcessExecuteModeEnum nodeExecuteEnum) {
        this.nodeExecuteEnum = nodeExecuteEnum;
    }

    public void setPolicyId(String policyId) {
        this.policyId = policyId;
    }

    public void setPolicyName(String policyName) {
        this.policyName = policyName;
    }

    public void setNodePermType(Integer nodePermType) {
        this.nodePermType = nodePermType;
    }

    public void setProcessTerm(ProcessTermEnum processTerm) {
        this.processTerm = processTerm;
    }

    public void setParameterCode(String parameterCode) {
        this.parameterCode = parameterCode;
    }

    public void setParameterName(String parameterName) {
        this.parameterName = parameterName;
    }

    public void setCustomTime(Integer customTime) {
        this.customTime = customTime;
    }

    public void setCustomTimeType(TimeTypeEnum customTimeType) {
        this.customTimeType = customTimeType;
    }

    public void setBeforeExpiredTime(Integer beforeExpiredTime) {
        this.beforeExpiredTime = beforeExpiredTime;
    }

    public void setBeforeExpiredTimeType(TimeTypeEnum beforeExpiredTimeType) {
        this.beforeExpiredTimeType = beforeExpiredTimeType;
    }

    public void setBeforeExpired(BeforeExpiredEnum beforeExpired) {
        this.beforeExpired = beforeExpired;
    }

    public void setAfterExpired(DealTermTypeEnum afterExpired) {
        this.afterExpired = afterExpired;
    }

    public void setRepealAlertTime(Integer repealAlertTime) {
        this.repealAlertTime = repealAlertTime;
    }

    public void setRepealAlertTimeType(TimeTypeEnum repealAlertTimeType) {
        this.repealAlertTimeType = repealAlertTimeType;
    }

    public void setMessageRemindUser(String messageRemindUser) {
        this.messageRemindUser = messageRemindUser;
    }

    public void setMessageReRemindUser(String messageReRemindUser) {
        this.messageReRemindUser = messageReRemindUser;
    }

    public void setDealTermUser(String dealTermUser) {
        this.dealTermUser = dealTermUser;
    }

    public void setReceiveImmediate(Boolean receiveImmediate) {
        this.receiveImmediate = receiveImmediate;
    }

    public void setFormOperationId(String formOperationId) {
        this.formOperationId = formOperationId;
    }

    public void setReadOnly(Boolean readOnly) {
        this.readOnly = readOnly;
    }

    public void setRepeatCount(Integer repeatCount) {
        this.repeatCount = repeatCount;
    }

    public void setAddNodeToMe(Boolean addNodeToMe) {
        this.addNodeToMe = addNodeToMe;
    }

    public void setAddNodeImmediate(Boolean addNodeImmediate) {
        this.addNodeImmediate = addNodeImmediate;
    }
}
