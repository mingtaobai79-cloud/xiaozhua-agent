/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.approval.BpmNodePermissionOperationSimpleDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionFilterResponseDto
 *  com.seeyon.bpm.dto.nodepermission.BpmNodePermissionOperationRequestDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.approval.BpmNodePermissionOperationSimpleDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionFilterResponseDto;
import com.seeyon.bpm.dto.nodepermission.BpmNodePermissionOperationRequestDto;
import java.util.List;

public interface BpmNodePermissionOperationAppService {
    public SingleResponse<BpmNodePermissionFilterResponseDto> getNodePermissionOperation(SingleRequest<BpmNodePermissionOperationRequestDto> var1);

    public ListResponse<BpmNodePermissionOperationSimpleDto> selectOperationSimpleByPermissionIds(SingleRequest<List<Long>> var1);
}
