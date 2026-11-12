/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.approval.BpmNodePermissionOperationSimpleDto
 */
package com.seeyon.bpm.dto.approval;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.approval.BpmNodePermissionOperationSimpleDto;
import java.util.List;

@DtoInfo(value="\u8282\u70b9\u6743\u9650\u8fd4\u56dedto")
public class BpmNodePermissionResponseDto
extends BaseDto {
    private static final long serialVersionUID = 6716240782138299773L;
    @DtoAttribute(value="\u6743\u9650ID", example="123456")
    private Long permissionId;
    @DtoAttribute(value="\u6743\u9650CODE", example="APPROVAL")
    private String permissionCode;
    @Deprecated
    @DtoAttribute(value="\u64cd\u4f5cID", example="123456")
    private Long operationId;
    @Deprecated
    @DtoAttribute(value="\u64cd\u4f5cCODE", example="NODE_ADD")
    private String operationCode;
    @Deprecated
    @DtoAttribute(value="\u610f\u89c1\u662f\u5426\u5fc5\u586b")
    private Boolean commentRequired;
    @Deprecated
    @DtoAttribute(value="\u64cd\u4f5c\u663e\u793a\u540d\u79f0", example="\u63d0\u4ea4")
    private String operationCaption;
    @DtoAttribute(value="\u6743\u9650\u64cd\u4f5c\u5217\u8868")
    List<BpmNodePermissionOperationSimpleDto> nodePermissionList;

    public String toString() {
        StringBuilder sb = new StringBuilder("{");
        if (this.permissionId != null) {
            sb.append("\"permissionId\":").append(this.permissionId).append(",");
        }
        if (this.permissionCode != null) {
            sb.append("\"permissionCode\":\"").append(this.permissionCode).append("\",");
        }
        if (this.operationId != null) {
            sb.append("\"operationId\":").append(this.operationId).append(",");
        }
        if (this.operationCode != null) {
            sb.append("\"operationCode\":\"").append(this.operationCode).append("\"}");
        }
        return sb.toString();
    }

    public Long getPermissionId() {
        return this.permissionId;
    }

    public String getPermissionCode() {
        return this.permissionCode;
    }

    @Deprecated
    public Long getOperationId() {
        return this.operationId;
    }

    @Deprecated
    public String getOperationCode() {
        return this.operationCode;
    }

    @Deprecated
    public Boolean getCommentRequired() {
        return this.commentRequired;
    }

    @Deprecated
    public String getOperationCaption() {
        return this.operationCaption;
    }

    public List<BpmNodePermissionOperationSimpleDto> getNodePermissionList() {
        return this.nodePermissionList;
    }

    public void setPermissionId(Long permissionId) {
        this.permissionId = permissionId;
    }

    public void setPermissionCode(String permissionCode) {
        this.permissionCode = permissionCode;
    }

    @Deprecated
    public void setOperationId(Long operationId) {
        this.operationId = operationId;
    }

    @Deprecated
    public void setOperationCode(String operationCode) {
        this.operationCode = operationCode;
    }

    @Deprecated
    public void setCommentRequired(Boolean commentRequired) {
        this.commentRequired = commentRequired;
    }

    @Deprecated
    public void setOperationCaption(String operationCaption) {
        this.operationCaption = operationCaption;
    }

    public void setNodePermissionList(List<BpmNodePermissionOperationSimpleDto> nodePermissionList) {
        this.nodePermissionList = nodePermissionList;
    }
}
