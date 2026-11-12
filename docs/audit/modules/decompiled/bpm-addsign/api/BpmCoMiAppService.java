/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.comi.CoMiDetailInfoDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.comi.CoMiDetailInfoDto;

public interface BpmCoMiAppService {
    default public SingleResponse<CoMiDetailInfoDto> getDetailInfo(SingleRequest<Long> request) {
        return null;
    }
}
