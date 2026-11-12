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

@DtoInfo(value="\u8282\u70b9\u64cd\u4f5cdto")
public class BpmOperationNodeDto
extends BaseDto {
    private static final long serialVersionUID = -4147677069802431018L;
    @DtoAttribute(value="\u9644\u8a00")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="\u4e8b\u9879ID", example="123456")
    private Long affairId;
    @DtoAttribute(value="\u9009\u4eba\u7ec4\u4ef6\u8fd4\u56de\u7684\u4fe1\u606f", example="[123,456]")
    private String selectPeoples;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650id", example="123456")
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
