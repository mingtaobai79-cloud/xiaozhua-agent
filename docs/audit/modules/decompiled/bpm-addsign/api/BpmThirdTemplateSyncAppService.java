/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmActivityResponsibilityDto
 *  com.seeyon.bpm.dto.BpmTemplateRecentDto
 *  com.seeyon.bpm.dto.BpmThirdTemplateCreateOrUpdateDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmActivityResponsibilityDto;
import com.seeyon.bpm.dto.BpmTemplateRecentDto;
import com.seeyon.bpm.dto.BpmThirdTemplateCreateOrUpdateDto;
import java.util.List;

public interface BpmThirdTemplateSyncAppService {
    public ListResponse<BpmThirdTemplateCreateOrUpdateDto> createBatch(SingleRequest<List<BpmThirdTemplateCreateOrUpdateDto>> var1);

    public SingleResponse<Void> updateBatch(SingleRequest<List<BpmThirdTemplateCreateOrUpdateDto>> var1);

    public SingleResponse<Void> createActivityResponsibilities(SingleRequest<List<BpmActivityResponsibilityDto>> var1);

    public SingleResponse<Void> createTemplateRecent(SingleRequest<BpmTemplateRecentDto> var1);
}
