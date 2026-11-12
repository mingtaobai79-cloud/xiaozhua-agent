/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.starter.udcrt.dto.BpmParameterDataDto
 *  com.seeyon.boot.starter.udcrt.dto.DataValidCreateFilterDto
 *  com.seeyon.boot.starter.udcrt.dto.DataValidUpdateFilterDto
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.message.BpmApprovalResultData
 *  com.seeyon.bpm.dto.message.event.BpmCancelEvent
 *  com.seeyon.bpm.dto.message.event.BpmStopEvent
 */
package com.seeyon.boot.starter.udcrt.api;

import com.seeyon.boot.starter.udcrt.dto.BpmParameterDataDto;
import com.seeyon.boot.starter.udcrt.dto.DataValidCreateFilterDto;
import com.seeyon.boot.starter.udcrt.dto.DataValidUpdateFilterDto;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.message.BpmApprovalResultData;
import com.seeyon.bpm.dto.message.event.BpmCancelEvent;
import com.seeyon.bpm.dto.message.event.BpmStopEvent;

public interface UdcBpmProcessService {
    public SingleResponse<BpmParameterDataDto> validUpdateFilterData(SingleRequest<DataValidUpdateFilterDto> var1);

    public SingleResponse<BpmParameterDataDto> validCreateFilterData(SingleRequest<DataValidCreateFilterDto> var1);

    public SingleResponse<Boolean> processBpmApproval(SingleRequest<BpmApprovalResultData> var1);

    public SingleResponse<Boolean> processBpmStop(SingleRequest<BpmStopEvent> var1);

    public SingleResponse<Boolean> processBpmCancel(SingleRequest<BpmCancelEvent> var1);

    public SingleResponse<Boolean> processBpmTakeBack(SingleRequest<BpmApprovalResultData> var1);

    @Deprecated
    public SingleResponse<BpmParameterDataDto> validFilterData(SingleRequest<DataValidUpdateFilterDto> var1);

    @Deprecated
    public SingleResponse<Integer> updateData(SingleRequest<DataValidUpdateFilterDto> var1);
}
