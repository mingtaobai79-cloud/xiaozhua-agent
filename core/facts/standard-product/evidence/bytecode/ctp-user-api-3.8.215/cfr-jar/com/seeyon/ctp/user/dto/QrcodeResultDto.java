/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 */
package com.seeyon.ctp.user.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.ctp.user.enums.QrcodeStatusEnum;
import java.io.Serializable;

public class QrcodeResultDto
implements Serializable {
    @DtoAttribute(value="\u72b6\u6001")
    private QrcodeStatusEnum status = QrcodeStatusEnum.GENERATED;
    @DtoAttribute(value="\u9884\u5236\u626b\u7801\u4eba")
    private Long userId;

    public QrcodeStatusEnum getStatus() {
        return this.status;
    }

    public Long getUserId() {
        return this.userId;
    }

    public void setStatus(QrcodeStatusEnum status) {
        this.status = status;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }
}

