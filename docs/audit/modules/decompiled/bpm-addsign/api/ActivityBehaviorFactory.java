/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.bpm.api.ext.activity.ActivityBehavior
 */
package com.seeyon.bpm.api.ext.activity;

import com.seeyon.bpm.api.ext.activity.ActivityBehavior;
import java.util.List;
import java.util.Set;

public interface ActivityBehaviorFactory {
    public List<ActivityBehavior> getActivityBehaviors(String var1);

    public String getActivityConfiguration(String var1);

    public Set<String> supportActivities();
}
