/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListRequest
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmVipSuperviseRunDto
 *  com.seeyon.bpm.dto.CommonResultDto
 *  com.seeyon.bpm.dto.SuperviseCancelFocusDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSkipDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListRequest;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmVipSuperviseRunDto;
import com.seeyon.bpm.dto.CommonResultDto;
import com.seeyon.bpm.dto.SuperviseCancelFocusDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSkipDto;

public interface BpmSuperviseAppService {
    public ListResponse<BpmVipSuperviseRunDto> search(ListRequest var1);

    public SingleResponse<Void> cancelFocus(SingleRequest<SuperviseCancelFocusDto> var1);

    public SingleResponse<CommonResultDto> skip(SingleRequest<BpmSkipDto> var1);
}
