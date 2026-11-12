/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmEventActivityCancelEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmEventActivityCancelEvent;

@MessageInfo(topic="BPM", value="节点取消激活消息", openApi=@OpenApi)
public class BpmEventActivityCancelMessage
extends BaseMessage<BpmEventActivityCancelEvent> {
    public static final String MSG_NAME = "节点取消激活消息";
}
