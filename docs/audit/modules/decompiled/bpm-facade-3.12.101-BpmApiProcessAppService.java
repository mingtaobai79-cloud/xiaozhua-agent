/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.bpm.dto.operation.openapi.BpmDiagramDetailInfoDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmDiagramDetailRequestDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.bpm.dto.operation.openapi.BpmDiagramDetailInfoDto;
import com.seeyon.bpm.dto.operation.openapi.BpmDiagramDetailRequestDto;

public interface BpmApiProcessAppService {
    public ListResponse<BpmDiagramDetailInfoDto> selectDiagramDetailByTemplateCodeAndVersion(SingleRequest<BpmDiagramDetailRequestDto> var1);
}
