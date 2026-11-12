/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.PageDtoRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalCreateDto
 *  com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalDeleteDto
 *  com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalDto
 *  com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalSelectDto
 *  com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalUpdateDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.PageDtoRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalCreateDto;
import com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalDeleteDto;
import com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalDto;
import com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalSelectDto;
import com.seeyon.bpm.dto.autoapproval.BpmAutoApprovalUpdateDto;

public interface BpmAutoApprovalAppService {
    public SingleResponse<Long> designerCreate(SingleRequest<BpmAutoApprovalCreateDto> var1);

    public SingleResponse<Boolean> designerUpdate(SingleRequest<BpmAutoApprovalUpdateDto> var1);

    public SingleResponse<Boolean> designerDelete(SingleRequest<BpmAutoApprovalDeleteDto> var1);

    public PageResponse<BpmAutoApprovalDto> designerSelect(PageDtoRequest<BpmAutoApprovalSelectDto> var1);
}
