/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmNodePermission4PageDto
 *  com.seeyon.bpm.dto.BpmPrefixForUdcDto
 *  com.seeyon.bpm.dto.BpmStopDto
 *  com.seeyon.bpm.dto.CommonResultDto
 *  com.seeyon.bpm.dto.approval.BpmApiSendApiResponseDto
 *  com.seeyon.bpm.dto.approval.BpmAsyncTriggerFlowUdcRequestDto
 *  com.seeyon.bpm.dto.approval.BpmNodePermissionRequestDto
 *  com.seeyon.bpm.dto.approval.BpmNodePermissionResponseDto
 *  com.seeyon.bpm.dto.approval.BpmOperationRepealUdcDto
 *  com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto
 *  com.seeyon.bpm.dto.approval.BpmSaveDraftUdcDto
 *  com.seeyon.bpm.dto.approval.BpmSaveDraftUdcResponseDto
 *  com.seeyon.bpm.dto.approval.BpmSendUdcDto
 *  com.seeyon.bpm.dto.approval.BpmTriggerFlowUdcRequestDto
 *  com.seeyon.bpm.dto.approval.BpmTriggerFlowUdcResponseDto
 */
package com.seeyon.bpm.api.udc;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmNodePermission4PageDto;
import com.seeyon.bpm.dto.BpmPrefixForUdcDto;
import com.seeyon.bpm.dto.BpmStopDto;
import com.seeyon.bpm.dto.CommonResultDto;
import com.seeyon.bpm.dto.approval.BpmApiSendApiResponseDto;
import com.seeyon.bpm.dto.approval.BpmAsyncTriggerFlowUdcRequestDto;
import com.seeyon.bpm.dto.approval.BpmNodePermissionRequestDto;
import com.seeyon.bpm.dto.approval.BpmNodePermissionResponseDto;
import com.seeyon.bpm.dto.approval.BpmOperationRepealUdcDto;
import com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto;
import com.seeyon.bpm.dto.approval.BpmSaveDraftUdcDto;
import com.seeyon.bpm.dto.approval.BpmSaveDraftUdcResponseDto;
import com.seeyon.bpm.dto.approval.BpmSendUdcDto;
import com.seeyon.bpm.dto.approval.BpmTriggerFlowUdcRequestDto;
import com.seeyon.bpm.dto.approval.BpmTriggerFlowUdcResponseDto;
import java.util.ArrayList;
import java.util.List;

public interface BpmUdcApiService {
    public SingleResponse<BpmApiSendApiResponseDto> sendForUdc(SingleRequest<BpmSendUdcDto> var1);

    default public SingleResponse<BpmSaveDraftUdcResponseDto> saveDraft(SingleRequest<BpmSaveDraftUdcDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmTriggerFlowUdcResponseDto> triggerFlowForUdc(SingleRequest<List<BpmTriggerFlowUdcRequestDto>> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<BpmPrefixForUdcResponseDto> prefixForUdc(SingleRequest<BpmPrefixForUdcDto> request) {
        return SingleResponse.from(null);
    }

    public SingleResponse<Void> repealForUdc(SingleRequest<BpmOperationRepealUdcDto> var1);

    public SingleResponse<CommonResultDto> stopForUdc(SingleRequest<BpmStopDto> var1);

    public SingleResponse<Void> deleteCaseByIdForUdc(SingleRequest<Long> var1, SingleRequest<Long> var2);

    default public ListResponse<BpmNodePermissionResponseDto> getNodePermissionOperation(SingleRequest<BpmNodePermissionRequestDto> request) {
        return ListResponse.from(null);
    }

    default public SingleResponse<BpmNodePermission4PageDto> getNodePermission(SingleRequest<BpmNodePermissionRequestDto> request) {
        return SingleResponse.from(null);
    }

    default public SingleResponse<Void> asyncTriggerFlowForUdc(SingleRequest<BpmAsyncTriggerFlowUdcRequestDto> request) {
        return SingleResponse.ok();
    }
}
