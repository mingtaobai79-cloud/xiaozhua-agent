/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.bpm.dto.caselog.BpmCaseLogDto
 *  com.seeyon.bpm.dto.caselog.BpmCaseLogSelectDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.bpm.dto.caselog.BpmCaseLogDto;
import com.seeyon.bpm.dto.caselog.BpmCaseLogSelectDto;

public interface BpmCaseLogAppService {
    public ListResponse<BpmCaseLogDto> selectByCaseId(SingleRequest<Long> var1);

    public ListResponse<BpmCaseLogDto> selectByDto(SingleRequest<BpmCaseLogSelectDto> var1);
}
