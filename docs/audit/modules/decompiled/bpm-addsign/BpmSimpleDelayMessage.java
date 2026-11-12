/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.DelayBaseMessage
 *  com.seeyon.bpm.dto.message.overtime.SimpleDelayData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.DelayBaseMessage;
import com.seeyon.bpm.dto.message.overtime.SimpleDelayData;

@MessageInfo(topic="BPM", value="精简过后的延迟消息")
public class BpmSimpleDelayMessage
extends DelayBaseMessage<SimpleDelayData> {
}
