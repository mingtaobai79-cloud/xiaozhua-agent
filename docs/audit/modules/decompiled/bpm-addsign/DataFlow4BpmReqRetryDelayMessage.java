/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.mq.DelayBaseMessage
 *  com.seeyon.boot.starter.dataflow.dto.DataFlow4BpmReqDto
 */
package com.seeyon.boot.starter.dataflow.mq;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.mq.DelayBaseMessage;
import com.seeyon.boot.starter.dataflow.dto.DataFlow4BpmReqDto;

@MessageInfo(topic="CMD_MSG", value="生单成功调用bpm接口异常重试消息")
public class DataFlow4BpmReqRetryDelayMessage
extends DelayBaseMessage<DataFlow4BpmReqDto> {
}
