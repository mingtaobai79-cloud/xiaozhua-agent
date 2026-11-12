/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.bpm.api.ext.activity.ActivityBehaviorChain
 */
package com.seeyon.bpm.api.ext.activity;

import com.seeyon.bpm.api.ext.activity.ActivityBehaviorChain;
import com.seeyon.bpm.api.ext.activity.BpmSupportOperation;

public interface ActivityBehavior
extends Comparable {
    default public int order() {
        return -20000;
    }

    public String getConfigId();

    public boolean preMatch(BpmSupportOperation var1, ActivityBehaviorChain var2);

    public boolean onActivityReady(BpmSupportOperation var1, ActivityBehaviorChain var2);

    public boolean onActivityFinish(BpmSupportOperation var1, ActivityBehaviorChain var2);

    public boolean onActivityCanceled(BpmSupportOperation var1, ActivityBehaviorChain var2);

    public boolean validateActivityAction(BpmSupportOperation var1, ActivityBehaviorChain var2);

    default public int compareTo(Object o) {
        ActivityBehavior activityBehavior = (ActivityBehavior)o;
        if (this.order() < activityBehavior.order()) {
            return -1;
        }
        if (this.order() == activityBehavior.order()) {
            return 0;
        }
        return 1;
    }
}
