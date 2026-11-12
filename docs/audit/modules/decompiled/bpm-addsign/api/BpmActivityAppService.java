/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmActivityRunDto
 *  com.seeyon.bpm.dto.BpmCaseActivityDto
 *  com.seeyon.bpm.dto.BpmCaseActivitySearchDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmActivityRunDto;
import com.seeyon.bpm.dto.BpmCaseActivityDto;
import com.seeyon.bpm.dto.BpmCaseActivitySearchDto;
import java.util.List;

public interface BpmActivityAppService {
    default public ListResponse<BpmActivityRunDto> selectAllByCaseId(SingleRequest<Long> request) {
        return null;
    }

    default public ListResponse<BpmCaseActivityDto> selectBpmCaseActivityByCaseId(SingleRequest<BpmCaseActivitySearchDto> request) {
        return null;
    }

    default public SingleResponse<Integer> create(SingleRequest<BpmActivityRunDto> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<Integer> createBatch(SingleRequest<List<BpmActivityRunDto>> request) {
        return SingleResponse.from((Object)0);
    }
}
