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

@DtoInfo(value="加签、减签请求参数对象")
public class ChangeNodeRequestDto
extends BpmBaseOperationDto {
    @DtoAttribute(value="流程Id,processJson，优先取processJson，没有就取processId在数据库中对应的流程图", example="687435655566")
    private Long processId;
    @DtoAttribute(value="流程图Json，和processId组合使用，优先取baseProcessXml，没有就取processId在数据库中对应的流程图", example="")
    private String processJson;
    @DtoAttribute(value="当前节点ID", example="1234567890")
    @NotNull
    private String currentActivityId;
    @DtoAttribute(value="当前WorkItem的ID", example="1234567890")
    private String workItemId;
    @DtoAttribute(value="当前操作的待办事项所属人id", example="1234567890", hidden=true)
    private Long currentOwnerId;
    @DtoAttribute(value="当前用户ID", example="987264829212", hidden=true, relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization")
    private Long userId;
    @DtoAttribute(value="操作类型", example="AddNode")
    @NotNull
    private ChangeTypeEnum changeTypeEnum;
    @DtoAttribute(value="是否插入日志", example="")
    private boolean needInsertLog = false;
    @DtoAttribute(value="前端加签界面选择的具体参数，减签的时候不需要", example="")
    private AddNodeParameterDto addNodeParameterDto;
    @DtoAttribute(value="需要减签的节点ID，只有减签的时候需要", example="")
    private List<String> deletedNodeIds;
    @DtoAttribute(value="替换节点信息", example="")
    private AddNodeOrgInfoDto replaceNodeDto;
    @DtoAttribute(value="加签节点节点属性修改")
    private List<AddNodeProcessTermParameterDto> modifyNodeTermParameterDtos = new ArrayList<AddNodeProcessTermParameterDto>();
    @DtoAttribute(value="前端表单数据")
    private Map<String, Object> formDataMap = new HashMap<String, Object>();
    @DtoAttribute(value="应用app")
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
