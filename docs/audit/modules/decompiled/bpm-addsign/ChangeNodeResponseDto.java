/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.AddNodeProcessTermParameterDto
 *  com.seeyon.bpm.dto.ChangeNodeLogDto
 *  com.seeyon.bpm.dto.formtemplate.ActivityOvertimeSetDto
 *  com.seeyon.bpm.dto.match.BpmUserDto
 *  org.apache.commons.collections.MapUtils
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.AddNodeProcessTermParameterDto;
import com.seeyon.bpm.dto.ChangeNodeLogDto;
import com.seeyon.bpm.dto.formtemplate.ActivityOvertimeSetDto;
import com.seeyon.bpm.dto.match.BpmUserDto;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.apache.commons.collections.MapUtils;

public class ChangeNodeResponseDto
extends BaseDto {
    @DtoAttribute(value="\u52a0\u7b7e/\u51cf\u7b7e\u64cd\u4f5c\u7684\u8fc7\u7a0b\u65e5\u5fd7\uff0c\u7528\u4e8e\u8bb0\u5f55\u6d41\u7a0b\u65e5\u5fd7\u7528", example="")
    private ChangeNodeLogDto changeNodeLogDto;
    @DtoAttribute(value="\u52a0\u7b7e/\u51cf\u7b7e\u540e\u7684\u6d41\u7a0b\u56feJSON\u5b57\u7b26\u4e32", example="")
    private String processJson;
    @DtoAttribute(value="\u662f\u5426\u6267\u884c\u52a0\u7b7e/\u51cf\u7b7e\u64cd\u4f5c\u6210\u529f", example="")
    private boolean success;
    @DtoAttribute(value="\u52a0\u7b7e/\u51cf\u7b7e\u5931\u8d25\u7684\u8fd4\u56de\u4fe1\u606f", example="")
    private String message;
    @DtoAttribute(value="\u9700\u8981\u6fc0\u6d3b\u7684\u8282\u70b9\u4fe1\u606f", example="")
    private Set<String> toActiveNodeIds = new HashSet<String>();
    @DtoAttribute(value="\u9700\u8981\u5220\u9664\u7684\u8282\u70b9\u4fe1\u606f", example="")
    private Set<String> toDeleteNodeIds = new HashSet<String>();
    @DtoAttribute(value="\u540e\u7eed\u53ef\u4ee5\u5220\u9664\u7684\u8282\u70b9id", example="")
    private List<String> canDeleteNodeIds = new ArrayList<String>();
    @DtoAttribute(value="\u52a0\u7b7e\u5230\u8282\u70b9\u5185\u4eba\u5458", example="")
    private List<BpmUserDto> innerAddMembers = new ArrayList<BpmUserDto>();
    @DtoAttribute(value="\u52a0\u7b7e\u8282\u70b9\u7684\u8282\u70b9\u4fe1\u606f")
    private List<AddNodeProcessTermParameterDto> addNodeProcessTermParameterDtos = new ArrayList<AddNodeProcessTermParameterDto>();
    @DtoAttribute(value="\u52a0\u7b7e\u8282\u70b9\u7684\u8d85\u671f\u8bbe\u7f6e\u4fe1\u606f,\u9700\u8981\u8c03\u7528\u65b9\u81ea\u5df1\u5165\u5e93", hidden=true)
    private List<ActivityOvertimeSetDto> activityOvertimeInfos = new ArrayList<ActivityOvertimeSetDto>();
    @DtoAttribute(value="\u52a0\u7b7e\u8282\u70b9\u7684\u8282\u70b9\u4fe1\u606f", hidden=true)
    private Map<String, String> activityIdParentLinkId = new HashMap<String, String>();
    @DtoAttribute(value="\u52a0\u7b7e\u56de\u5230\u6211\u7684\u8282\u70b9id")
    private String addNodeToMeNodeId;
    @DtoAttribute(value="\u52a0\u7b7e\u7acb\u5373\u6536\u5230-\u62c6\u5206\u51fa\u7684\u8282\u70b9id")
    private String splitNodeId;
    @DtoAttribute(value="\u52a0\u7b7e\u7acb\u5373\u6536\u5230-\u62c6\u5206\u51fa\u7684\u8282\u70b9\u540d\u79f0")
    private String splitNodeName;

    public void addActivityIdParentLInkId(String activityId, String linkId) {
        this.activityIdParentLinkId.put(activityId, linkId);
    }

    public void addActivityIdParentLInkId(Map<String, String> activityIdAndParentLinkId) {
        if (MapUtils.isEmpty(activityIdAndParentLinkId)) {
            return;
        }
        this.activityIdParentLinkId.putAll(activityIdAndParentLinkId);
    }

    public ChangeNodeLogDto getChangeNodeLogDto() {
        return this.changeNodeLogDto;
    }

    public String getProcessJson() {
        return this.processJson;
    }

    public boolean isSuccess() {
        return this.success;
    }

    public String getMessage() {
        return this.message;
    }

    public Set<String> getToActiveNodeIds() {
        return this.toActiveNodeIds;
    }

    public Set<String> getToDeleteNodeIds() {
        return this.toDeleteNodeIds;
    }

    public List<String> getCanDeleteNodeIds() {
        return this.canDeleteNodeIds;
    }

    public List<BpmUserDto> getInnerAddMembers() {
        return this.innerAddMembers;
    }

    public List<AddNodeProcessTermParameterDto> getAddNodeProcessTermParameterDtos() {
        return this.addNodeProcessTermParameterDtos;
    }

    public List<ActivityOvertimeSetDto> getActivityOvertimeInfos() {
        return this.activityOvertimeInfos;
    }

    public Map<String, String> getActivityIdParentLinkId() {
        return this.activityIdParentLinkId;
    }

    public String getAddNodeToMeNodeId() {
        return this.addNodeToMeNodeId;
    }

    public String getSplitNodeId() {
        return this.splitNodeId;
    }

    public String getSplitNodeName() {
        return this.splitNodeName;
    }

    public void setChangeNodeLogDto(ChangeNodeLogDto changeNodeLogDto) {
        this.changeNodeLogDto = changeNodeLogDto;
    }

    public void setProcessJson(String processJson) {
        this.processJson = processJson;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setToActiveNodeIds(Set<String> toActiveNodeIds) {
        this.toActiveNodeIds = toActiveNodeIds;
    }

    public void setToDeleteNodeIds(Set<String> toDeleteNodeIds) {
        this.toDeleteNodeIds = toDeleteNodeIds;
    }

    public void setCanDeleteNodeIds(List<String> canDeleteNodeIds) {
        this.canDeleteNodeIds = canDeleteNodeIds;
    }

    public void setInnerAddMembers(List<BpmUserDto> innerAddMembers) {
        this.innerAddMembers = innerAddMembers;
    }

    public void setAddNodeProcessTermParameterDtos(List<AddNodeProcessTermParameterDto> addNodeProcessTermParameterDtos) {
        this.addNodeProcessTermParameterDtos = addNodeProcessTermParameterDtos;
    }

    public void setActivityOvertimeInfos(List<ActivityOvertimeSetDto> activityOvertimeInfos) {
        this.activityOvertimeInfos = activityOvertimeInfos;
    }

    public void setActivityIdParentLinkId(Map<String, String> activityIdParentLinkId) {
        this.activityIdParentLinkId = activityIdParentLinkId;
    }

    public void setAddNodeToMeNodeId(String addNodeToMeNodeId) {
        this.addNodeToMeNodeId = addNodeToMeNodeId;
    }

    public void setSplitNodeId(String splitNodeId) {
        this.splitNodeId = splitNodeId;
    }

    public void setSplitNodeName(String splitNodeName) {
        this.splitNodeName = splitNodeName;
    }
}
