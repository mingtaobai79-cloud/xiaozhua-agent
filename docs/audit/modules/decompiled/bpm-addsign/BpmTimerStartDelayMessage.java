/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.DelayBaseMessage
 *  com.seeyon.bpm.dto.message.BpmTimerStartData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.DelayBaseMessage;
import com.seeyon.bpm.dto.message.BpmTimerStartData;

@MessageInfo(topic="BPM", value="定时开始节点延迟消息")
public class BpmTimerStartDelayMessage
extends DelayBaseMessage<BpmTimerStartData> {
}
