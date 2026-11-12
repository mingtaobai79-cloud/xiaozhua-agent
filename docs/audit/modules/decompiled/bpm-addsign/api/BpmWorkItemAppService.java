/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmWorkItemDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmWorkItemDto;
import java.util.ArrayList;
import java.util.List;

public interface BpmWorkItemAppService {
    default public SingleResponse<Integer> create(SingleRequest<BpmWorkItemDto> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<Integer> createBatch(SingleRequest<List<BpmWorkItemDto>> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<BpmWorkItemDto> selectById(SingleRequest<Long> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmWorkItemDto> selectByCaseId(SingleRequest<Long> request) {
        return ListResponse.from(new ArrayList());
    }
}
