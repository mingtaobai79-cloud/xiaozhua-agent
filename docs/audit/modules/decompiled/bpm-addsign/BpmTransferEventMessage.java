/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmTransferEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmTransferEvent;

@MessageInfo(topic="BPM", value="流程移交消息", openApi=@OpenApi)
public class BpmTransferEventMessage
extends BaseMessage<BpmTransferEvent> {
}
