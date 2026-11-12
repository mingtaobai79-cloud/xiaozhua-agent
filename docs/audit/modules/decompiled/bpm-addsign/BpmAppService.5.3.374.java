/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.ChangeNodeResponseDto
 *  com.seeyon.bpm.dto.CommonResultDto
 *  com.seeyon.bpm.dto.DeleteDraftReqDto
 *  com.seeyon.bpm.dto.SecurityCheckDto
 *  com.seeyon.bpm.dto.SimpleChangeProcessRequestDto
 *  com.seeyon.bpm.dto.approval.BpmBatchReqDto
 *  com.seeyon.bpm.dto.approval.BpmBatchResponseDto
 *  com.seeyon.bpm.dto.fullinfo.BpmCaseFullInfo
 *  com.seeyon.bpm.dto.fullinfo.BpmCaseFullInfoSearch
 *  com.seeyon.bpm.dto.message.msg.BpmItemInfoDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmAddExecuteUserDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmCancelItemDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmConsultDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmHastenDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmHastenResponseDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmInformDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmMonitorRunDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmMonitorRunResultDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmMultipleReplaceDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmPauseDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmPauseResponseDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmReliveDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmReliveFullDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmRepealDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmReplaceDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSaveDraftDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSaveDraftResultDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSendDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSendResultDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmStepBackDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmStopDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSubmitDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSubmitResultDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmTakeBackDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.ChangeNodeResponseDto;
import com.seeyon.bpm.dto.CommonResultDto;
import com.seeyon.bpm.dto.DeleteDraftReqDto;
import com.seeyon.bpm.dto.SecurityCheckDto;
import com.seeyon.bpm.dto.SimpleChangeProcessRequestDto;
import com.seeyon.bpm.dto.approval.BpmBatchReqDto;
import com.seeyon.bpm.dto.approval.BpmBatchResponseDto;
import com.seeyon.bpm.dto.fullinfo.BpmCaseFullInfo;
import com.seeyon.bpm.dto.fullinfo.BpmCaseFullInfoSearch;
import com.seeyon.bpm.dto.message.msg.BpmItemInfoDto;
import com.seeyon.bpm.dto.operation.openapi.BpmAddExecuteUserDto;
import com.seeyon.bpm.dto.operation.openapi.BpmCancelItemDto;
import com.seeyon.bpm.dto.operation.openapi.BpmConsultDto;
import com.seeyon.bpm.dto.operation.openapi.BpmHastenDto;
import com.seeyon.bpm.dto.operation.openapi.BpmHastenResponseDto;
import com.seeyon.bpm.dto.operation.openapi.BpmInformDto;
import com.seeyon.bpm.dto.operation.openapi.BpmMonitorRunDto;
import com.seeyon.bpm.dto.operation.openapi.BpmMonitorRunResultDto;
import com.seeyon.bpm.dto.operation.openapi.BpmMultipleReplaceDto;
import com.seeyon.bpm.dto.operation.openapi.BpmPauseDto;
import com.seeyon.bpm.dto.operation.openapi.BpmPauseResponseDto;
import com.seeyon.bpm.dto.operation.openapi.BpmReliveDto;
import com.seeyon.bpm.dto.operation.openapi.BpmReliveFullDto;
import com.seeyon.bpm.dto.operation.openapi.BpmRepealDto;
import com.seeyon.bpm.dto.operation.openapi.BpmReplaceDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSaveDraftDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSaveDraftResultDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSendDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSendResultDto;
import com.seeyon.bpm.dto.operation.openapi.BpmStepBackDto;
import com.seeyon.bpm.dto.operation.openapi.BpmStopDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSubmitDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSubmitResultDto;
import com.seeyon.bpm.dto.operation.openapi.BpmTakeBackDto;
import java.util.ArrayList;

public interface BpmAppService {
    public SingleResponse<BpmSendResultDto> send(SingleRequest<BpmSendDto> var1);

    public SingleResponse<BpmSaveDraftResultDto> saveDraft(SingleRequest<BpmSaveDraftDto> var1);

    public SingleResponse<BpmSubmitResultDto> submit(SingleRequest<BpmSubmitDto> var1);

    public SingleResponse<CommonResultDto> stepBack(SingleRequest<BpmStepBackDto> var1);

    public SingleResponse<CommonResultDto> repeal(SingleRequest<BpmRepealDto> var1);

    public SingleResponse<CommonResultDto> stop(SingleRequest<BpmStopDto> var1);

    public SingleResponse<CommonResultDto> takeBack(SingleRequest<BpmTakeBackDto> var1);

    public SingleResponse<CommonResultDto> replace(SingleRequest<BpmReplaceDto> var1);

    default public SingleResponse<CommonResultDto> consult(SingleRequest<BpmConsultDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmHastenResponseDto> hasten(SingleRequest<BpmHastenDto> request) {
        return ListResponse.from(new ArrayList());
    }

    public SingleResponse<CommonResultDto> multipleReplace(SingleRequest<BpmMultipleReplaceDto> var1);

    public ListResponse<BpmPauseResponseDto> pause(SingleRequest<BpmPauseDto> var1);

    public ListResponse<BpmPauseResponseDto> cancelPause(SingleRequest<BpmPauseDto> var1);

    public SingleResponse<CommonResultDto> superviseRelive(SingleRequest<BpmReliveDto> var1);

    public SingleResponse<CommonResultDto> superviseReliveFull(SingleRequest<BpmReliveFullDto> var1);

    public SingleResponse<CommonResultDto> inform(SingleRequest<BpmInformDto> var1);

    public ListResponse<BpmItemInfoDto> addExecuteMember(SingleRequest<BpmAddExecuteUserDto> var1);

    public SingleResponse<CommonResultDto> cancelItems(SingleRequest<BpmCancelItemDto> var1);

    public ListResponse<BpmBatchResponseDto> batchDeal(SingleRequest<BpmBatchReqDto> var1);

    public SingleResponse<BpmCaseFullInfo> selectFullCaseInfo(SingleRequest<BpmCaseFullInfoSearch> var1);

    public SingleResponse<ChangeNodeResponseDto> counterSignNode(SingleRequest<SimpleChangeProcessRequestDto> var1);

    public SingleResponse<ChangeNodeResponseDto> addNode(SingleRequest<SimpleChangeProcessRequestDto> var1);

    default public SingleResponse<BpmMonitorRunResultDto> monitorNodeRun(SingleRequest<BpmMonitorRunDto> request) {
        return SingleResponse.buildProcessingResponse();
    }

    default public SingleResponse<Boolean> check(SingleRequest<SecurityCheckDto> request) {
        return SingleResponse.from((Object)false);
    }

    @Deprecated
    public SingleResponse<Void> deleteDraft(SingleRequest<Long> var1);

    public SingleResponse<Void> deleteDraftAffair(SingleRequest<DeleteDraftReqDto> var1);
}
