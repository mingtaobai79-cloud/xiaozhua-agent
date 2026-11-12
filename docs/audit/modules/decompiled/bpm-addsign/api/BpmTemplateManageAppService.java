/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmAppInfoDto
 *  com.seeyon.bpm.dto.BpmBatchAuthDto
 *  com.seeyon.bpm.dto.BpmGrayUpdateDto
 *  com.seeyon.bpm.dto.BpmTemplateDto
 *  com.seeyon.bpm.dto.BpmTemplateNodePerScopeDto
 *  com.seeyon.bpm.dto.FormalAuthTemplateQueryDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmAppInfoDto;
import com.seeyon.bpm.dto.BpmBatchAuthDto;
import com.seeyon.bpm.dto.BpmGrayUpdateDto;
import com.seeyon.bpm.dto.BpmTemplateDto;
import com.seeyon.bpm.dto.BpmTemplateNodePerScopeDto;
import com.seeyon.bpm.dto.FormalAuthTemplateQueryDto;
import java.util.List;

public interface BpmTemplateManageAppService {
    public SingleResponse<Void> grayAuthTemplate(SingleRequest<BpmGrayUpdateDto> var1);

    public SingleResponse<Void> closeLowerVersionGrayAndStarted(SingleRequest<List<BpmAppInfoDto>> var1);

    public SingleResponse<Void> startByAppName(SingleRequest<BpmAppInfoDto> var1);

    public ListResponse<BpmTemplateDto> selectFormalAuthTemplateList(SingleRequest<Long> var1);

    public ListResponse<BpmTemplateDto> selectFormalAuthTemplateListByQueryDto(SingleRequest<FormalAuthTemplateQueryDto> var1);

    public ListResponse<BpmTemplateDto> selectGrayAuthTemplateList(SingleRequest<String> var1);

    public SingleResponse<Void> updateAuth(SingleRequest<BpmBatchAuthDto> var1);

    public SingleResponse<Void> invalidAppTemplatesByAppGuid(SingleRequest<Long> var1);

    default public SingleResponse<Void> configNodePermissionScope(SingleRequest<BpmTemplateNodePerScopeDto> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<Void> framePublish(SingleRequest<String> appName) {
        return SingleResponse.ok();
    }

    default public SingleResponse<Void> clearDefaultFrameCache(SingleRequest<String> appName) {
        return SingleResponse.ok();
    }
}
