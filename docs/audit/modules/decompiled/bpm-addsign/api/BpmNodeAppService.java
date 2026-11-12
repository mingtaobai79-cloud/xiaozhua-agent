/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.ParameterInfo
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.bpm.dto.BpmNodeDto
 *  com.seeyon.bpm.dto.BpmNodeSearchDto
 *  com.seeyon.bpm.dto.BpmNodeSimpleDto
 *  com.seeyon.bpm.dto.BpmPreNodeSearchDto
 *  com.seeyon.bpm.dto.policy.NodePolicySearchDto
 *  com.seeyon.bpm.dto.policy.NodeProperties
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.annotation.ParameterInfo;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.bpm.dto.BpmNodeDto;
import com.seeyon.bpm.dto.BpmNodeSearchDto;
import com.seeyon.bpm.dto.BpmNodeSimpleDto;
import com.seeyon.bpm.dto.BpmPreNodeSearchDto;
import com.seeyon.bpm.dto.policy.NodePolicySearchDto;
import com.seeyon.bpm.dto.policy.NodeProperties;

public interface BpmNodeAppService {
    default public PageResponse<BpmNodeDto> selectPageByConditions(@ParameterInfo(value="\u5206\u9875\u67e5\u8be2\u53c2\u6570") PageRequest request) {
        return null;
    }

    default public ListResponse<BpmNodeDto> selectByTemplateAndActivityType(SingleRequest<BpmNodeSearchDto> searchDtoSingleRequest) {
        return null;
    }

    default public ListResponse<BpmNodeSimpleDto> selectRunningProcessPreNode(SingleRequest<BpmPreNodeSearchDto> searchDtoSingleRequest) {
        return null;
    }

    default public ListResponse<NodeProperties> selectNodePolicy(SingleRequest<NodePolicySearchDto> request) {
        return null;
    }
}
