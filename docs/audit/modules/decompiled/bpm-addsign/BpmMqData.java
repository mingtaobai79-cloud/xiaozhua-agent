/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDynamicAppDto
 *  com.seeyon.bpm.dto.message.BpmMqDataType
 */
package com.seeyon.bpm.dto.message;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDynamicAppDto;
import com.seeyon.bpm.dto.message.BpmMqDataType;

@DtoInfo(value="bpm消息基类")
public abstract class BpmMqData
extends BaseDynamicAppDto {
    @DtoAttribute(value="消息类型", example="PROCESS_STARTED")
    private BpmMqDataType dataType;

    public BpmMqDataType getDataType() {
        return this.dataType;
    }

    public void setDataType(BpmMqDataType dataType) {
        this.dataType = dataType;
    }
}
