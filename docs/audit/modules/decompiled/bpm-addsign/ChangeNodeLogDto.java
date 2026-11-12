/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.enums.ChangeTypeEnum
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.enums.ChangeTypeEnum;

@DtoInfo(value="\u52a0\u7b7e\u3001\u51cf\u7b7e\u7b49\u6539\u53d8\u6d41\u7a0b\u7684\u65e5\u5fd7\u5bf9\u8c61")
public class ChangeNodeLogDto
extends BaseDto {
    @DtoAttribute(value="\u52a0\u7b7e\u7c7b\u578b", example="")
    private ChangeTypeEnum changeTypeEnum;
    @DtoAttribute(value="\u64cd\u4f5c\u4eba", example="")
    private String handlerId;
    @DtoAttribute(value="\u6d41\u7a0bID", example="")
    private Long processId;
    @DtoAttribute(value="\u8282\u70b9\u540d\u79f0\u548c\u8282\u70b9\u6743\u9650\u540d\u79f0", example="\u5f20\u4e09\uff08\u534f\u540c\uff09")
    private String nodeAndPolicyNames;
    @DtoAttribute(value="\u8282\u70b9\u540d\u79f0", example="")
    private String nodeNames;
    @DtoAttribute(value="\u65b0\u7684\u8282\u70b9\u540d\u79f0", example="")
    private String newNodeNames;

    public ChangeTypeEnum getChangeTypeEnum() {
        return this.changeTypeEnum;
    }

    public String getHandlerId() {
        return this.handlerId;
    }

    public Long getProcessId() {
        return this.processId;
    }

    public String getNodeAndPolicyNames() {
        return this.nodeAndPolicyNames;
    }

    public String getNodeNames() {
        return this.nodeNames;
    }

    public String getNewNodeNames() {
        return this.newNodeNames;
    }

    public void setChangeTypeEnum(ChangeTypeEnum changeTypeEnum) {
        this.changeTypeEnum = changeTypeEnum;
    }

    public void setHandlerId(String handlerId) {
        this.handlerId = handlerId;
    }

    public void setProcessId(Long processId) {
        this.processId = processId;
    }

    public void setNodeAndPolicyNames(String nodeAndPolicyNames) {
        this.nodeAndPolicyNames = nodeAndPolicyNames;
    }

    public void setNodeNames(String nodeNames) {
        this.nodeNames = nodeNames;
    }

    public void setNewNodeNames(String newNodeNames) {
        this.newNodeNames = newNodeNames;
    }
}
