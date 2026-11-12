/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.splitimport.BpmSplitPrepareDto
 *  com.seeyon.bpm.dto.splitimport.BpmTemplateBaseDto
 */
package com.seeyon.bpm.api.udc;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.splitimport.BpmSplitPrepareDto;
import com.seeyon.bpm.dto.splitimport.BpmTemplateBaseDto;

public interface BpmApiSplitImportAppService {
    public ListResponse<BpmTemplateBaseDto> selectTemplateByAppName(SingleRequest<String> var1);

    public SingleResponse<String> prepareApp(SingleRequest<BpmSplitPrepareDto> var1);

    public SingleResponse<Void> splitImport(SingleRequest<String> var1);
}
