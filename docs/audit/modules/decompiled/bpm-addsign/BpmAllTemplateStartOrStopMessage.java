/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmAllTemplateStartOrStopEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmAllTemplateStartOrStopEvent;

@MessageInfo(topic="BPM", value="流程所有模板启用停用消息", openApi=@OpenApi)
public class BpmAllTemplateStartOrStopMessage
extends BaseMessage<BpmAllTemplateStartOrStopEvent> {
}
