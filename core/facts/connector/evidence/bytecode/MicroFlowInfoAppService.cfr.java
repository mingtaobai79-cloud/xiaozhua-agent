/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.udc.dto.microflow.MicroFlowIntegrationAppInfoDto
 */
package com.seeyon.udc.api;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.udc.dto.microflow.MicroFlowIntegrationAppInfoDto;
import java.util.List;
import java.util.Map;

public interface MicroFlowInfoAppService {
    @Deprecated
    public SingleResponse<Map<String, List<String>>> findCallConnectorAppService(SingleRequest<Long> var1);

    public SingleResponse<MicroFlowIntegrationAppInfoDto> findCallIntegrationAppService(SingleRequest<Long> var1);
}
