/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.boot.starter.dataflow.dto.DataFlow4BpmReqDto
 */
package com.seeyon.boot.starter.dataflow.mq;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.boot.starter.dataflow.dto.DataFlow4BpmReqDto;

@MessageInfo(topic="CMD_MSG", value="生单成功调用bpm发起流程消息")
public class DataFlow4BpmReqMessage
extends BaseMessage<DataFlow4BpmReqDto> {
}
