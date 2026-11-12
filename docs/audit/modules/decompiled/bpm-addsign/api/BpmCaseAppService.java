/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.ParameterInfo
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmCaseDto
 *  com.seeyon.bpm.dto.BpmDeleteCaseDto
 *  com.seeyon.bpm.dto.expression.BpmExpressionDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmCaseInfoSearchDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.annotation.ParameterInfo;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmCaseDto;
import com.seeyon.bpm.dto.BpmDeleteCaseDto;
import com.seeyon.bpm.dto.expression.BpmExpressionDto;
import com.seeyon.bpm.dto.operation.openapi.BpmCaseInfoSearchDto;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public interface BpmCaseAppService {
    public SingleResponse<BpmCaseDto> selectCaseById(SingleRequest<Long> var1);

    public SingleResponse<Long> selectMainCaseBySubCaseId(SingleRequest<Long> var1);

    default public SingleResponse<String> deleteCaseByIds(SingleRequest<BpmDeleteCaseDto> bpmDeleteCaseDtoSingleRequest) {
        return null;
    }

    default public SingleResponse<BpmCaseDto> selectById(SingleRequest<Long> request) {
        return null;
    }

    default public ListResponse<BpmCaseDto> selectByIds(SingleRequest<List<Long>> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<BpmCaseDto> selectBpmCaseByFormRecordId(SingleRequest<BpmCaseInfoSearchDto> request) {
        return null;
    }

    default public PageResponse<BpmCaseDto> selectByPageCondition(PageRequest request) {
        return null;
    }

    default public SingleResponse<BpmCaseDto> selectCascadeById(SingleRequest<Long> request) {
        return null;
    }

    default public ListResponse<BpmCaseDto> selectCascadeByIds(SingleRequest<List<Long>> request) {
        return null;
    }

    default public PageResponse<BpmCaseDto> dynamicSelect(SingleRequest<ProxyParamDto> request) {
        return null;
    }

    default public PageResponse<BpmCaseDto> dynamicJoinSelect(SingleRequest<ProxyJoinParamDto> request) {
        return null;
    }

    default public PageResponse<BpmCaseDto> selectPageByConditions(@ParameterInfo(value="\u5206\u9875\u67e5\u8be2\u53c2\u6570") PageRequest request) {
        return null;
    }

    default public SingleResponse<String> refreshCaseTitleById(SingleRequest<Long> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<BpmCaseDto> selectCascadeByConditions(SingleRequest<QueryConditionDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmCaseDto> selectCascadeListByConditions(SingleRequest<QueryConditionDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<BpmCaseDto> getCascadeDefaultValue(SingleRequest<Void> request) {
        return SingleResponse.from((Object)new BpmCaseDto());
    }

    default public ListResponse<String> selectCaseAttachmentList(SingleRequest<Long> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Integer> create(SingleRequest<BpmCaseDto> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<Integer> createBatch(SingleRequest<List<BpmCaseDto>> request) {
        return SingleResponse.from((Object)0);
    }

    default public SingleResponse<BpmCaseDto> selectByIdDisplayName(SingleRequest<Long> id, SingleRequest<Set<String>> fieldSet) {
        return SingleResponse.from((Object)new BpmCaseDto());
    }

    default public ListResponse<BpmCaseDto> selectByIdsDisplayName(SingleRequest<List<Long>> ids, SingleRequest<Set<String>> fieldSet) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Void> updateCase(SingleRequest<BpmCaseDto> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<BpmExpressionDto> selectExpression(SingleRequest<Long> idRequest) {
        return SingleResponse.from(null);
    }
}
