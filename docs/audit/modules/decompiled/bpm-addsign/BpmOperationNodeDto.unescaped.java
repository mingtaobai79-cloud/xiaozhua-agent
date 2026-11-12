/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.BpmCommentDto
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.BpmCommentDto;

@DtoInfo(value="节点操作dto")
public class BpmOperationNodeDto
extends BaseDto {
    private static final long serialVersionUID = -4147677069802431018L;
    @DtoAttribute(value="附言")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="事项ID", example="123456")
    private Long affairId;
    @DtoAttribute(value="选人组件返回的信息", example="[123,456]")
    private String selectPeoples;
    @DtoAttribute(value="节点权限id", example="123456")
    private Long nodePermissionId;

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public Long getAffairId() {
        return this.affairId;
    }

    public String getSelectPeoples() {
        return this.selectPeoples;
    }

    public Long getNodePermissionId() {
        return this.nodePermissionId;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }

    public void setAffairId(Long affairId) {
        this.affairId = affairId;
    }

    public void setSelectPeoples(String selectPeoples) {
        this.selectPeoples = selectPeoples;
    }

    public void setNodePermissionId(Long nodePermissionId) {
        this.nodePermissionId = nodePermissionId;
    }
}
