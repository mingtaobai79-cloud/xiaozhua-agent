/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.MessageInfo
 *  com.seeyon.boot.annotation.OpenApi
 *  com.seeyon.boot.mq.BaseMessage
 *  com.seeyon.bpm.dto.message.BpmVipSuperviseChangeData
 */
package com.seeyon.bpm.dto.message.msg;

import com.seeyon.boot.annotation.MessageInfo;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.mq.BaseMessage;
import com.seeyon.bpm.dto.message.BpmVipSuperviseChangeData;

@MessageInfo(topic="BPM", value="vip督办预审模式数据变化消息", openApi=@OpenApi)
public class BpmVipSuperviseChangeMessage
extends BaseMessage<BpmVipSuperviseChangeData> {
}
