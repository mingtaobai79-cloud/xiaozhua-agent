/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.event.BpmDeployEvent
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.event.BpmDeployEvent;

@MessageInfo(topic="BPM", value="BPM发布消息")
public class BpmDeployMessage
extends BaseMessage<BpmDeployEvent> {
    private static final long serialVersionUID = -6649546426780676086L;
}
