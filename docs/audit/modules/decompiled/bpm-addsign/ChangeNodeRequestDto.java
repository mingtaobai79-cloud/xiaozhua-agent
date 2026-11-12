/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.AddNodeOrgInfoDto
 *  com.seeyon.bpm.dto.AddNodeParameterDto
 *  com.seeyon.bpm.dto.AddNodeProcessTermParameterDto
 *  com.seeyon.bpm.dto.BpmBaseOperationDto
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.AddNodeOrgInfoDto;
import com.seeyon.bpm.dto.AddNodeParameterDto;
import com.seeyon.bpm.dto.AddNodeProcessTermParameterDto;
import com.seeyon.bpm.dto.BpmBaseOperationDto;
import com.seeyon.bpm.enums.ChangeTypeEnum;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.validation.constraints.NotNull;

@DtoInfo(value="\u52a0\u7b7e\u3001\u51cf\u7b7e\u8bf7\u6c42\u53c2\u6570\u5bf9\u8c61")
public class ChangeNodeRequestDto
extends BpmBaseOperationDto {
    @DtoAttribute(value="\u6d41\u7a0bId,processJson\uff0c\u4f18\u5148\u53d6processJson\uff0c\u6ca1\u6709\u5c31\u53d6processId\u5728\u6570\u636e\u5e93\u4e2d\u5bf9\u5e94\u7684\u6d41\u7a0b\u56fe", example="687435655566")
    private Long processId;
    @DtoAttribute(value="\u6d41\u7a0b\u56feJson\uff0c\u548cprocessId\u7ec4\u5408\u4f7f\u7528\uff0c\u4f18\u5148\u53d6baseProcessXml\uff0c\u6ca1\u6709\u5c31\u53d6processId\u5728\u6570\u636e\u5e93\u4e2d\u5bf9\u5e94\u7684\u6d41\u7a0b\u56fe", example="")
    private String processJson;
    @DtoAttribute(value="\u5f53\u524d\u8282\u70b9ID", example="1234567890")
    @NotNull
    private String currentActivityId;
    @DtoAttribute(value="\u5f53\u524dWorkItem\u7684ID", example="1234567890")
    private String workItemId;
    @DtoAttribute(value="\u5f53\u524d\u64cd\u4f5c\u7684\u5f85\u529e\u4e8b\u9879\u6240\u5c5e\u4ebaid", example="1234567890", hidden=true)
    private Long currentOwnerId;
    @DtoAttribute(value="\u5f53\u524d\u7528\u6237ID", example="987264829212", hidden=true, relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization")
    private Long userId;
    @DtoAttribute(value="\u64cd\u4f5c\u7c7b\u578b", example="AddNode")
    @NotNull
    private ChangeTypeEnum changeTypeEnum;
    @DtoAttribute(value="\u662f\u5426\u63d2\u5165\u65e5\u5fd7", example="")
    private boolean needInsertLog = false;
    @DtoAttribute(value="\u524d\u7aef\u52a0\u7b7e\u754c\u9762\u9009\u62e9\u7684\u5177\u4f53\u53c2\u6570\uff0c\u51cf\u7b7e\u7684\u65f6\u5019\u4e0d\u9700\u8981", example="")
    private AddNodeParameterDto addNodeParameterDto;
    @DtoAttribute(value="\u9700\u8981\u51cf\u7b7e\u7684\u8282\u70b9ID\uff0c\u53ea\u6709\u51cf\u7b7e\u7684\u65f6\u5019\u9700\u8981", example="")
    private List<String> deletedNodeIds;
    @DtoAttribute(value="\u66ff\u6362\u8282\u70b9\u4fe1\u606f", example="")
    private AddNodeOrgInfoDto replaceNodeDto;
    @DtoAttribute(value="\u52a0\u7b7e\u8282\u70b9\u8282\u70b9\u5c5e\u6027\u4fee\u6539")
    private List<AddNodeProcessTermParameterDto> modifyNodeTermParameterDtos = new ArrayList<AddNodeProcessTermParameterDto>();
    @DtoAttribute(value="\u524d\u7aef\u8868\u5355\u6570\u636e")
    private Map<String, Object> formDataMap = new HashMap<String, Object>();
    @DtoAttribute(value="\u5e94\u7528app")
    private String applicationName;

    public Long getProcessId() {
        return this.processId;
    }

    public String getProcessJson() {
        return this.processJson;
    }

    public String getCurrentActivityId() {
        return this.currentActivityId;
    }

    public String getWorkItemId() {
        return this.workItemId;
    }

    public Long getCurrentOwnerId() {
        return this.currentOwnerId;
    }

    public Long getUserId() {
        return this.userId;
    }

    public ChangeTypeEnum getChangeTypeEnum() {
        return this.changeTypeEnum;
    }

    public boolean isNeedInsertLog() {
        return this.needInsertLog;
    }

    public AddNodeParameterDto getAddNodeParameterDto() {
        return this.addNodeParameterDto;
    }

    public List<String> getDeletedNodeIds() {
        return this.deletedNodeIds;
    }

    public AddNodeOrgInfoDto getReplaceNodeDto() {
        return this.replaceNodeDto;
    }

    public List<AddNodeProcessTermParameterDto> getModifyNodeTermParameterDtos() {
        return this.modifyNodeTermParameterDtos;
    }

    public Map<String, Object> getFormDataMap() {
        return this.formDataMap;
    }

    public String getApplicationName() {
        return this.applicationName;
    }

    public void setProcessId(Long processId) {
        this.processId = processId;
    }

    public void setProcessJson(String processJson) {
        this.processJson = processJson;
    }

    public void setCurrentActivityId(String currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    public void setWorkItemId(String workItemId) {
        this.workItemId = workItemId;
    }

    public void setCurrentOwnerId(Long currentOwnerId) {
        this.currentOwnerId = currentOwnerId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setChangeTypeEnum(ChangeTypeEnum changeTypeEnum) {
        this.changeTypeEnum = changeTypeEnum;
    }

    public void setNeedInsertLog(boolean needInsertLog) {
        this.needInsertLog = needInsertLog;
    }

    public void setAddNodeParameterDto(AddNodeParameterDto addNodeParameterDto) {
        this.addNodeParameterDto = addNodeParameterDto;
    }

    public void setDeletedNodeIds(List<String> deletedNodeIds) {
        this.deletedNodeIds = deletedNodeIds;
    }

    public void setReplaceNodeDto(AddNodeOrgInfoDto replaceNodeDto) {
        this.replaceNodeDto = replaceNodeDto;
    }

    public void setModifyNodeTermParameterDtos(List<AddNodeProcessTermParameterDto> modifyNodeTermParameterDtos) {
        this.modifyNodeTermParameterDtos = modifyNodeTermParameterDtos;
    }

    public void setFormDataMap(Map<String, Object> formDataMap) {
        this.formDataMap = formDataMap;
    }

    public void setApplicationName(String applicationName) {
        this.applicationName = applicationName;
    }
}
