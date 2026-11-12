/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.common.Constants
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmNodePermissionAddDto
 *  com.seeyon.bpm.dto.BpmNodePermissionDetailDto
 *  com.seeyon.bpm.dto.BpmNodePermissionFullFieldDto
 *  com.seeyon.bpm.dto.BpmNodePermissionInitDto
 *  com.seeyon.bpm.dto.BpmNodePermissionMaxOrderNumQueryDto
 *  com.seeyon.bpm.dto.BpmNodePermissionQueryDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionBindDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionQueryConditionDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionSearchRequestDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionSearchResponseDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.common.Constants;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmNodePermissionAddDto;
import com.seeyon.bpm.dto.BpmNodePermissionDetailDto;
import com.seeyon.bpm.dto.BpmNodePermissionFullFieldDto;
import com.seeyon.bpm.dto.BpmNodePermissionInitDto;
import com.seeyon.bpm.dto.BpmNodePermissionMaxOrderNumQueryDto;
import com.seeyon.bpm.dto.BpmNodePermissionQueryDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionBindDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionQueryConditionDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionSearchRequestDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionSearchResponseDto;
import java.util.ArrayList;
import java.util.List;

public interface BpmApiNodePermissionAppService {
    public SingleResponse<Void> bpmNodePermissionHandel(SingleRequest<BpmNodePermissionInitDto> var1);

    public SingleResponse<BpmNodePermissionDetailDto> selectNodePermissionById(SingleRequest<BpmNodePermissionQueryDto> var1);

    default public ListResponse<BpmNodePermissionDetailDto> selectNodePermissionListByIds(SingleRequest<BpmNodePermissionQueryDto> request) {
        return ListResponse.from(new ArrayList());
    }

    public SingleResponse<Long> savePermission(SingleRequest<BpmNodePermissionAddDto> var1);

    public ListResponse<Long> savePermissionList(SingleRequest<List<BpmNodePermissionAddDto>> var1);

    default public ListResponse<BpmNodePermissionSearchResponseDto> queryPermissionList(SingleRequest<BpmNodePermissionSearchRequestDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Void> configNodePermissionBind(SingleRequest<List<BpmNodePermissionBindDto>> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmNodePermissionDetailDto> selectNodePermissionDetailListByIds(SingleRequest<List<Long>> request) {
        return ListResponse.from(new ArrayList());
    }

    default public ListResponse<BpmNodePermissionFullFieldDto> selectNodePermissionListByConditions(SingleRequest<BpmNodePermissionQueryConditionDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Void> createOrUpdateNodePermissionBatch(SingleRequest<List<BpmNodePermissionFullFieldDto>> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<Integer> getMaxOrderNumber(SingleRequest<BpmNodePermissionMaxOrderNumQueryDto> request) {
        return SingleResponse.from((Object)Constants.INTEGER_ZERO);
    }
}
