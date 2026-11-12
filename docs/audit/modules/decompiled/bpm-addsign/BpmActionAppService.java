/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.activity.BpmActivitySubmitDto
 *  com.seeyon.bpm.dto.activity.BpmActivityTakeBackDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmSubmitResultDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.activity.BpmActivitySubmitDto;
import com.seeyon.bpm.dto.activity.BpmActivityTakeBackDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSubmitResultDto;

public interface BpmActionAppService {
    default public SingleResponse<BpmSubmitResultDto> activitySubmit(SingleRequest<BpmActivitySubmitDto> singleRequest) {
        return null;
    }

    default public SingleResponse<Void> activityStepBack(SingleRequest<BpmActivityTakeBackDto> singleRequest) {
        return null;
    }
}
