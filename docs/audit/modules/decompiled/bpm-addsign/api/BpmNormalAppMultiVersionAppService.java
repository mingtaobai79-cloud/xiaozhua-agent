/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmUpdateApplicationToSpecifiedInstitutionDto
 *  com.seeyon.bpm.dto.CurrentHighestVersionRequestDto
 *  com.seeyon.bpm.dto.CurrentHighestVersionResponseDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmUpdateApplicationToSpecifiedInstitutionDto;
import com.seeyon.bpm.dto.CurrentHighestVersionRequestDto;
import com.seeyon.bpm.dto.CurrentHighestVersionResponseDto;

public interface BpmNormalAppMultiVersionAppService {
    public ListResponse<CurrentHighestVersionResponseDto> selectCurrentHighestVersionBatch(SingleRequest<CurrentHighestVersionRequestDto> var1);

    default public SingleResponse<Void> updateNormalApplicationToSpecifiedInstitution(SingleRequest<BpmUpdateApplicationToSpecifiedInstitutionDto> request) {
        return SingleResponse.ok();
    }
}
