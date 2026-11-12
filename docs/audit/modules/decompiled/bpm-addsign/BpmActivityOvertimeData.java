/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.bpm.dto.message.BpmDelayMqData
 */
package com.seeyon.bpm.dto.message.overtime;

import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.bpm.dto.message.BpmDelayMqData;
import com.seeyon.bpm.dto.message.overtime.ActivityOvertimeMessage;

@DtoInfo(value="节点超期延时消息")
public class BpmActivityOvertimeData
extends BpmDelayMqData {
    private ActivityOvertimeMessage activityOvertimeMessage;

    public ActivityOvertimeMessage getActivityOvertimeMessage() {
        return this.activityOvertimeMessage;
    }

    public void setActivityOvertimeMessage(ActivityOvertimeMessage activityOvertimeMessage) {
        this.activityOvertimeMessage = activityOvertimeMessage;
    }
}
