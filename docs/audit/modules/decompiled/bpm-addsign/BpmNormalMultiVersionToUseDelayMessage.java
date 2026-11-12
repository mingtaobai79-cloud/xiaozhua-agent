/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.DelayBaseMessage
 *  com.seeyon.bpm.dto.message.BpmNormalMultiVersionToUseDelayData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.DelayBaseMessage;
import com.seeyon.bpm.dto.message.BpmNormalMultiVersionToUseDelayData;

@MessageInfo(topic="BPM", value="普通应用即将使用延迟消息")
public class BpmNormalMultiVersionToUseDelayMessage
extends DelayBaseMessage<BpmNormalMultiVersionToUseDelayData> {
}
