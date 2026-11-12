/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmImportDto
 *  com.seeyon.bpm.dto.transport.BpmExportInitDataDto
 *  com.seeyon.bpm.dto.transport.BpmInitDataDto
 *  com.seeyon.bpm.dto.transport.BpmInitParamDto
 *  com.seeyon.bpm.dto.transport.BpmSaveAsDto
 *  com.seeyon.bpm.dto.transport.BpmTransportRequestDto
 */
package com.seeyon.bpm.api.udc;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmImportDto;
import com.seeyon.bpm.dto.transport.BpmExportInitDataDto;
import com.seeyon.bpm.dto.transport.BpmInitDataDto;
import com.seeyon.bpm.dto.transport.BpmInitParamDto;
import com.seeyon.bpm.dto.transport.BpmSaveAsDto;
import com.seeyon.bpm.dto.transport.BpmTransportRequestDto;
import java.util.ArrayList;

public interface BpmApiTransportAppService {
    public SingleResponse<Void> saveAs(SingleRequest<BpmSaveAsDto> var1);

    public SingleResponse<BpmExportInitDataDto> getApplicationInitData(SingleRequest<BpmInitParamDto> var1);

    public SingleResponse<String> getApplicationInitDataAsync(SingleRequest<BpmInitParamDto> var1);

    public SingleResponse<String> exportTemplateInfo(SingleRequest<BpmInitDataDto> var1);

    public SingleResponse<Void> importTemplateInfo(SingleRequest<BpmImportDto> var1);

    default public ListResponse<String> selectUsedConnectorByAppName(SingleRequest<String> appNameRequest) {
        return ListResponse.from(new ArrayList());
    }

    public SingleResponse<String> asyncTransportRequest(SingleRequest<BpmTransportRequestDto> var1);
}
