/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.google.common.collect.Lists
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  javax.validation.Valid
 */
package com.seeyon.ctp.user.dto.menu;

import com.google.common.collect.Lists;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import java.util.List;
import javax.validation.Valid;

@DtoInfo(value="\u524d\u7aef\u7528\u6237\u5bfc\u822a\u680f\u7528\u5230\u7684dto")
public class CtpUserThirdNavFrontDto
extends BaseDto {
    private static final long serialVersionUID = 7020235073887850881L;
    @DtoAttribute(value="\u83dc\u5355Id", example="123456", hidden=true)
    private Long id;
    @DtoAttribute(value="\u540d\u79f0", example="\u8d44\u6e90\u540d\u79f0")
    private String title;
    @DtoAttribute(value="\u56fe\u6807", example="icon")
    private String icon = "";
    @DtoAttribute(value="\u8df3\u8f6c\u94fe\u63a5", example="/demo-order/order-info")
    private String url;
    @DtoAttribute(value="\u6253\u5f00\u65b9\u5f0f:WORKSPACE,NEWWINDOW,MAIN", example="WORKSPACE")
    private String openType = "";
    @DtoAttribute(value="\u6240\u5c5e\u5e94\u7528", example="portal")
    private String appId;
    @Valid
    @DtoAttribute(value="\u5b50\u8282\u70b9")
    private List<CtpUserThirdNavFrontDto> children = Lists.newArrayList();
    @DtoAttribute(value="\u7236\u83dc\u5355id", example="26565685986454")
    private Long parentId;
    @DtoAttribute(value="\u6570\u636e\u578b\u8d44\u6e90\u7684\u7c7b\u578b", example="BIZ_HOME")
    private String dataType;

    public void setId(Long id) {
        this.id = id;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setIcon(String icon) {
        this.icon = icon;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public void setOpenType(String openType) {
        this.openType = openType;
    }

    public void setAppId(String appId) {
        this.appId = appId;
    }

    public void setChildren(List<CtpUserThirdNavFrontDto> children) {
        this.children = children;
    }

    public void setParentId(Long parentId) {
        this.parentId = parentId;
    }

    public void setDataType(String dataType) {
        this.dataType = dataType;
    }

    public Long getId() {
        return this.id;
    }

    public String getTitle() {
        return this.title;
    }

    public String getIcon() {
        return this.icon;
    }

    public String getUrl() {
        return this.url;
    }

    public String getOpenType() {
        return this.openType;
    }

    public String getAppId() {
        return this.appId;
    }

    public List<CtpUserThirdNavFrontDto> getChildren() {
        return this.children;
    }

    public Long getParentId() {
        return this.parentId;
    }

    public String getDataType() {
        return this.dataType;
    }
}

