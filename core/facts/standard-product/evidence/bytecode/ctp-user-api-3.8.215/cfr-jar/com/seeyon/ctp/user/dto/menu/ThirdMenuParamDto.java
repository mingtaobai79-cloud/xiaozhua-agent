/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 */
package com.seeyon.ctp.user.dto.menu;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;

@DtoInfo(value="\u4e09\u65b9\u83dc\u5355\u8bf7\u6c42\u53c2\u6570")
public class ThirdMenuParamDto
extends BaseDto {
    private static final long serialVersionUID = -1487542722299819207L;
    @DtoAttribute(value="\u6bcf\u6b21\u67e5\u8be2\u83dc\u5355\u5927\u5c0f", example="20")
    private Integer size;
    @DtoAttribute(value="\u5f00\u59cb\u7684\u7d22\u5f15", example="0")
    private Integer startIndex;
    @DtoAttribute(value="\u673a\u6784id", example="343543")
    private Long orgId;
    @DtoAttribute(value="\u7528\u6237id", example="343543")
    private Long userId;
    @DtoAttribute(value="\u662f\u5426\u662f\u95e8\u6237\u65b0\u6837\u5f0f", example="false")
    private Boolean isNewStyle = false;

    public Integer getSize() {
        return this.size;
    }

    public Integer getStartIndex() {
        return this.startIndex;
    }

    public Long getOrgId() {
        return this.orgId;
    }

    public Long getUserId() {
        return this.userId;
    }

    public Boolean getIsNewStyle() {
        return this.isNewStyle;
    }

    public void setSize(Integer size) {
        this.size = size;
    }

    public void setStartIndex(Integer startIndex) {
        this.startIndex = startIndex;
    }

    public void setOrgId(Long orgId) {
        this.orgId = orgId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setIsNewStyle(Boolean isNewStyle) {
        this.isNewStyle = isNewStyle;
    }
}

