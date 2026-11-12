/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.DelayBaseMessage
 *  com.seeyon.bpm.dto.message.BpmAutoNodeDelayData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.DelayBaseMessage;
import com.seeyon.bpm.dto.message.BpmAutoNodeDelayData;

@MessageInfo(topic="BPM", value="自动节点延迟消息")
public class BpmAutoNodeDelayMessage
extends DelayBaseMessage<BpmAutoNodeDelayData> {
    private static final long serialVersionUID = 4945295709307558878L;
}
