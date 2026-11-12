/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.enums.BeforeExpiredEnum
 *  com.seeyon.bpm.enums.DealTermTypeEnum
 *  com.seeyon.bpm.enums.ProcessExecuteEnum
 *  com.seeyon.bpm.enums.ProcessTermEnum
 *  com.seeyon.bpm.enums.TimeTypeEnum
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.enums.BeforeExpiredEnum;
import com.seeyon.bpm.enums.DealTermTypeEnum;
import com.seeyon.bpm.enums.ProcessExecuteEnum;
import com.seeyon.bpm.enums.ProcessTermEnum;
import com.seeyon.bpm.enums.TimeTypeEnum;
import javax.validation.constraints.NotNull;

@DtoInfo(value="\u52a0\u7b7e\u754c\u9762\u6d41\u7a0b\u671f\u9650\u53c2\u6570")
public class AddNodeProcessTermParameterDto
extends BaseDto {
    @DtoAttribute(value="\u8282\u70b9id", example="")
    private String activityId;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650ID", example="")
    private String policyId;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650\u540d\u79f0", example="")
    private String policyName;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650\u7c7b\u578bCode", example="")
    private Integer nodePermType;
    @DtoAttribute(value="\u6267\u884c\u6a21\u5f0f \u5168\u4f53\u5e76\u53d1 \u7ade\u4e89", example="ALL_PARALLEL")
    private ProcessExecuteEnum processExecuteEnum;
    @DtoAttribute(value="\u8282\u70b9\u671f\u9650", example="NO_SETTING")
    @NotNull
    private ProcessTermEnum processTerm;
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
    @NotNull
    private BeforeExpiredEnum beforeExpired = BeforeExpiredEnum.NO_OPERATION;
    @DtoAttribute(value="\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c", example="NO_OPERATION")
    private DealTermTypeEnum afterExpired;
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
    @DtoAttribute(value="\u5230\u671f\u91cd\u590d\u63d0\u9192\u6b21\u6570\uff0c\u53ea\u6709\u8282\u70b9\u5230\u671f\u540e\u64cd\u4f5c\u9009\u62e9\u7684\u662f\u6d88\u606f\u63d0\u9192-\u91cd\u590d\u63d0\u9192\u8be5\u53c2\u6570\u624d\u6709\u6548", example="1")
    private Integer repeatCount;
    @DtoAttribute(value="\u8868\u5355\u6743\u9650ID", example="")
    private String formOperationId;

    public String getActivityId() {
        return this.activityId;
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

    public ProcessExecuteEnum getProcessExecuteEnum() {
        return this.processExecuteEnum;
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

    public Integer getRepeatCount() {
        return this.repeatCount;
    }

    public String getFormOperationId() {
        return this.formOperationId;
    }

    public void setActivityId(String activityId) {
        this.activityId = activityId;
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

    public void setProcessExecuteEnum(ProcessExecuteEnum processExecuteEnum) {
        this.processExecuteEnum = processExecuteEnum;
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

    public void setRepeatCount(Integer repeatCount) {
        this.repeatCount = repeatCount;
    }

    public void setFormOperationId(String formOperationId) {
        this.formOperationId = formOperationId;
    }
}
