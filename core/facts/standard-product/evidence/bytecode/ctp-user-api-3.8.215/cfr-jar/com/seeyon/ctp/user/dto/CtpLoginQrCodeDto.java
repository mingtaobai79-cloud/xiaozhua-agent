/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import java.util.Date;

@DtoInfo(value="\u4e8c\u7ef4\u7801\u751f\u6210")
public class CtpLoginQrCodeDto
extends BaseDto {
    private static final long serialVersionUID = 2565302127531211448L;
    @DtoAttribute(value="\u4e8c\u7ef4\u7801\u503c")
    private String qrValue;
    @DtoAttribute(value="\u4e1a\u52a1id")
    private Long objectId;
    @DtoAttribute(value="\u8fc7\u671f\u65f6\u95f4")
    private Date expireTime;
    @DtoAttribute(value="\u4e8c\u7ef4\u7801\u5b58\u50a8\u7684storageKey")
    private String storageKey;
    @DtoAttribute(value="\u4e8c\u7ef4\u7801base64\u6570\u636e")
    private String imageStr;

    public String getQrValue() {
        return this.qrValue;
    }

    public Long getObjectId() {
        return this.objectId;
    }

    public Date getExpireTime() {
        return this.expireTime;
    }

    public String getStorageKey() {
        return this.storageKey;
    }

    public String getImageStr() {
        return this.imageStr;
    }

    public void setQrValue(String qrValue) {
        this.qrValue = qrValue;
    }

    public void setObjectId(Long objectId) {
        this.objectId = objectId;
    }

    public void setExpireTime(Date expireTime) {
        this.expireTime = expireTime;
    }

    public void setStorageKey(String storageKey) {
        this.storageKey = storageKey;
    }

    public void setImageStr(String imageStr) {
        this.imageStr = imageStr;
    }
}

