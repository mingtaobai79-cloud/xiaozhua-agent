/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.boot.mq;

import com.seeyon.boot.mq.BaseMessage;

public abstract class DelayBaseMessage<T>
extends BaseMessage {
    private Long executeTime;

    public Long getExecuteTime() {
        return this.executeTime;
    }

    public void setExecuteTime(Long executeTime) {
        this.executeTime = executeTime;
    }
}
