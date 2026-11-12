/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.boot.mq;

import java.io.Serializable;

public abstract class BaseMessage<T>
implements Serializable {
    private static final long serialVersionUID = 5621640812292987951L;
    private T data;
    private Integer partition;

    public T getData() {
        return this.data;
    }

    public Integer getPartition() {
        return this.partition;
    }

    public void setData(T data) {
        this.data = data;
    }

    public void setPartition(Integer partition) {
        this.partition = partition;
    }
}
