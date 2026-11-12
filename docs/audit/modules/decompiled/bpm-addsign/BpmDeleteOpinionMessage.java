/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmDeleteOpinionEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmDeleteOpinionEvent;

@MessageInfo(topic="BPM", value="流程意见删除消息")
public class BpmDeleteOpinionMessage
extends BaseMessage<BpmDeleteOpinionEvent> {
    private static final long serialVersionUID = -5324701636069593145L;
}
