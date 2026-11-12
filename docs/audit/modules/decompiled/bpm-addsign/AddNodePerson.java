/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import javax.validation.constraints.NotNull;

@DtoInfo(value="\u52a0\u7b7e/\u4f1a\u7b7e\u5177\u4f53\u53c2\u6570")
public class AddNodePerson
extends BaseDto {
    @NotNull
    @DtoAttribute(value="\u9009\u62e9\u4eba\u5458ID", example="1", relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto", relationApp="organization", customs={@Custom(name="openApiCustom", properties={@CustomAttribute(name="escapeAttributeNameAlias", value="userCode")})})
    private Long userId;

    public Long getUserId() {
        return this.userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }
}
