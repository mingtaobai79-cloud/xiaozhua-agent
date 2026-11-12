/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.message.BpmDelayMqData
 *  com.seeyon.bpm.dto.message.overtime.ProcessOvertimeMessage
 */
package com.seeyon.bpm.dto.message.overtime;

import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.message.BpmDelayMqData;
import com.seeyon.bpm.dto.message.overtime.ProcessOvertimeMessage;

@DtoInfo(value="流程超期延时消息")
public class BpmProcessOvertimeData
extends BpmDelayMqData {
    private ProcessOvertimeMessage processOvertimeMessage;

    public ProcessOvertimeMessage getProcessOvertimeMessage() {
        return this.processOvertimeMessage;
    }

    public void setProcessOvertimeMessage(ProcessOvertimeMessage processOvertimeMessage) {
        this.processOvertimeMessage = processOvertimeMessage;
    }
}
