/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmActivityFinishEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmActivityFinishEvent;

@MessageInfo(topic="BPM", value="节点完成消息", openApi=@OpenApi)
public class BpmActivityFinishMessage
extends BaseMessage<BpmActivityFinishEvent> {
    public static final String MSG_NAME = "节点完成消息";
}
