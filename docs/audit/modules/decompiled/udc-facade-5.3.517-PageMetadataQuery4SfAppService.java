/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.udc.dto.meta.UdcApplicationMetaData4SfDto
 */
package com.seeyon.udc.api;

import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.udc.dto.meta.UdcApplicationMetaData4SfDto;

public interface PageMetadataQuery4SfAppService {
    public SingleResponse<UdcApplicationMetaData4SfDto> selectAppMetaDataByAppName(SingleRequest<String> var1);
}
