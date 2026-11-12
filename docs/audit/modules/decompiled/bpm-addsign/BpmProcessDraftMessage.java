/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmProcessDraftEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmProcessDraftEvent;

@MessageInfo(topic="BPM", value="流程保存待发消息", openApi=@OpenApi)
public class BpmProcessDraftMessage
extends BaseMessage<BpmProcessDraftEvent> {
    private static final long serialVersionUID = 2223965008122823100L;
}
