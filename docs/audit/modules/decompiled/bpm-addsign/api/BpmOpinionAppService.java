/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageDtoRequest
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.opinion.BpmDeleteOpinionDto
 *  com.seeyon.bpm.dto.opinion.BpmInputOpinionDto
 *  com.seeyon.bpm.dto.opinion.BpmOpinionDataDto
 *  com.seeyon.bpm.dto.opinion.BpmOpinionOpenApiNodeResponseDto
 *  com.seeyon.bpm.dto.opinion.BpmOpinionRequestDto
 *  com.seeyon.bpm.dto.opinion.BpmOpinionUpdateDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageDtoRequest;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.opinion.BpmDeleteOpinionDto;
import com.seeyon.bpm.dto.opinion.BpmInputOpinionDto;
import com.seeyon.bpm.dto.opinion.BpmOpinionDataDto;
import com.seeyon.bpm.dto.opinion.BpmOpinionOpenApiNodeResponseDto;
import com.seeyon.bpm.dto.opinion.BpmOpinionRequestDto;
import com.seeyon.bpm.dto.opinion.BpmOpinionUpdateDto;
import java.util.List;

public interface BpmOpinionAppService {
    public ListResponse<BpmOpinionOpenApiNodeResponseDto> selectOpinionGroupByActivityNodeWithObjectId(PageDtoRequest<BpmOpinionRequestDto> var1);

    default public SingleResponse<Integer> createBatch(SingleRequest<List<BpmInputOpinionDto>> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<Integer> create(SingleRequest<BpmOpinionDataDto> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<Integer> createBatchOpinion(SingleRequest<List<BpmOpinionDataDto>> request) {
        return SingleResponse.from((Object)0);
    }

    public SingleResponse<Integer> deleteOpinion(SingleRequest<BpmDeleteOpinionDto> var1);

    default public SingleResponse<Void> updateOpinion(SingleRequest<BpmOpinionUpdateDto> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<Void> adminDeleteOpinion(SingleRequest<Long> request) {
        return SingleResponse.ok();
    }
}
