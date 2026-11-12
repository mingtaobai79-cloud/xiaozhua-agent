/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.AppOperateLogQueryDto
 *  com.seeyon.bpm.dto.BpmApplicationOperateLogInfoDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.AppOperateLogQueryDto;
import com.seeyon.bpm.dto.BpmApplicationOperateLogInfoDto;
import java.util.List;

public interface BpmApplicationOperateLogAppService {
    public SingleResponse<Void> saveApplicationOperateLog(SingleRequest<BpmApplicationOperateLogInfoDto> var1);

    public SingleResponse<BpmApplicationOperateLogInfoDto> selectNewestLogInfo(SingleRequest<AppOperateLogQueryDto> var1);

    public SingleResponse<Void> updateAppLogs(SingleRequest<List<BpmApplicationOperateLogInfoDto>> var1);
}
