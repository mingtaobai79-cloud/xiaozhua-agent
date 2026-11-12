/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.edoc.BpmEdocDetailResponseDto
 *  com.seeyon.bpm.dto.edoc.BpmEdocSummaryDetailParamDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.edoc.BpmEdocDetailResponseDto;
import com.seeyon.bpm.dto.edoc.BpmEdocSummaryDetailParamDto;

public interface BpmDetailAppService {
    public SingleResponse<BpmEdocDetailResponseDto> selectDetail(SingleRequest<BpmEdocSummaryDetailParamDto> var1);
}
