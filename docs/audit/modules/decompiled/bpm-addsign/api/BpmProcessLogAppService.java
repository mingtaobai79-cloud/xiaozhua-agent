/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.ParameterInfo
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmProcessLogDto
 *  com.seeyon.bpm.dto.SearchProcessLogInfoDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.annotation.ParameterInfo;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmProcessLogDto;
import com.seeyon.bpm.dto.SearchProcessLogInfoDto;
import java.util.List;

public interface BpmProcessLogAppService {
    public SingleResponse<Long> create(SingleRequest<BpmProcessLogDto> var1);

    public SingleResponse<Integer> createBatch(SingleRequest<List<BpmProcessLogDto>> var1);

    public ListResponse<BpmProcessLogDto> selectLogList(SingleRequest<Long> var1);

    default public SingleResponse<Integer> createBatchProcessLog(SingleRequest<List<BpmProcessLogDto>> request) {
        return null;
    }

    public ListResponse<BpmProcessLogDto> selectOriginalI18nLogList(SingleRequest<Long> var1);

    public ListResponse<BpmProcessLogDto> selectLogOriginalListByCaseIds(SingleRequest<SearchProcessLogInfoDto> var1);

    default public PageResponse<BpmProcessLogDto> selectPageByConditions(@ParameterInfo(value="\u5206\u9875\u67e5\u8be2\u53c2\u6570") PageRequest request) {
        return null;
    }
}
