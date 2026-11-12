/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import java.util.Date;

@DtoInfo(value="工作流待办信息基础表")
public class BpmItemInfoDto
extends BaseDto {
    @DtoAttribute(value="事项Id", example="")
    private Long itemId;
    private static final long serialVersionUID = -3205501578868343371L;
    @DtoAttribute(value="事项所属人", example="zhangsan", relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization", customs={@Custom(name="openApiCustom", properties={@CustomAttribute(name="escapeAttributeNameAlias", value="memberCode")})})
    private Long memberId;
    @DtoAttribute(value="用户名称", example="")
    private String memberName;
    @DtoAttribute(value="事项创建时间")
    private Date receiveTime;

    public Long getItemId() {
        return this.itemId;
    }

    public Long getMemberId() {
        return this.memberId;
    }

    public String getMemberName() {
        return this.memberName;
    }

    public Date getReceiveTime() {
        return this.receiveTime;
    }

    public void setItemId(Long itemId) {
        this.itemId = itemId;
    }

    public void setMemberId(Long memberId) {
        this.memberId = memberId;
    }

    public void setMemberName(String memberName) {
        this.memberName = memberName;
    }

    public void setReceiveTime(Date receiveTime) {
        this.receiveTime = receiveTime;
    }
}
