/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.BpmDetectionData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.BpmDetectionData;

@MessageInfo(topic="BPM", value="流程一致性检测消息")
public class BpmDetectionMessage
extends BaseMessage<BpmDetectionData> {
}
