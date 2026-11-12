/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.bpm.api.ext.activity;

import java.util.Map;

public interface BpmSupportOperation {
    public String getConfigId();

    public Map<String, Object> getParameters();

    public void setParameter(String var1, Object var2);

    public Object getConfigurationValue(String var1);

    public Map<String, Object> getAllConfigurationValues();

    public Long getCaseId();

    public Long getActivityId();

    public String getActivityPolicyId();

    public String getAppName();

    public Long getTemplateId();

    public String getFormRecordId();

    public String getRootEntityName();

    public String getApplicationName();

    public String getSubject();

    public Long getStartUserId();

    public Long getCurrentUserId();
}
