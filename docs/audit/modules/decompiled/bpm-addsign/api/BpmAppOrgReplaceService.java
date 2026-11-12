/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmAppOrgReplaceDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmAppOrgReplaceDto;

public interface BpmAppOrgReplaceService {
    public SingleResponse<Void> replace(SingleRequest<BpmAppOrgReplaceDto> var1);
}
