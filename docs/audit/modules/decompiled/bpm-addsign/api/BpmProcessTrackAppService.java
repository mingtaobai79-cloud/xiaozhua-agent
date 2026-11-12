/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmProcessTrackReqDto
 *  com.seeyon.bpm.dto.BpmProcessTrackResDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmProcessTrackReqDto;
import com.seeyon.bpm.dto.BpmProcessTrackResDto;

public interface BpmProcessTrackAppService {
    public PageResponse<BpmProcessTrackResDto> selectProcessTrackList(SingleRequest<BpmProcessTrackReqDto> var1);

    default public SingleResponse<Integer> countAttentionForBadge(SingleRequest<BpmProcessTrackReqDto> request) {
        return SingleResponse.from((Object)0);
    }
}
