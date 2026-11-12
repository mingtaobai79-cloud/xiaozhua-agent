/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.bpm.dto.BpmAppInfoDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.bpm.dto.BpmAppInfoDto;
import java.util.Collections;
import java.util.List;

public interface BpmApiPermissionAppService {
    default public boolean checkApplicationPermission(BpmAppInfoDto appInfoDto) {
        return true;
    }

    default public List<Long> getCurrentOrgHierarchicalAppGuid() {
        return Collections.emptyList();
    }

    default public boolean isProcessFragmentEnabled() {
        return false;
    }
}
