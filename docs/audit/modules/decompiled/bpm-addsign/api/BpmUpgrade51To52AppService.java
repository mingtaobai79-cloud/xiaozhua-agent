/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.upgrade.UdcExtensionPlanRequestDto
 */
package com.seeyon.bpm.api.upgrade;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.upgrade.UdcExtensionPlanRequestDto;
import java.util.List;

public interface BpmUpgrade51To52AppService {
    public SingleResponse<Void> upgradeExtensionPlan(SingleRequest<List<UdcExtensionPlanRequestDto>> var1);
}
