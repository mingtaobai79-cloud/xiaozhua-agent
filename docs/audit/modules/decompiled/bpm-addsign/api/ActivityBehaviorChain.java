/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.bpm.api.ext.activity;

import com.seeyon.bpm.api.ext.activity.BpmSupportOperation;

public interface ActivityBehaviorChain {
    public <T> T doBehaviorChain(BpmSupportOperation var1, Class<T> var2);

    public boolean hasNext();
}
