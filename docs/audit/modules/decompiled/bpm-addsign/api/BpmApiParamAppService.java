/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmDataTypeDto
 *  com.seeyon.bpm.dto.BpmParameterDataDto
 *  com.seeyon.bpm.dto.BpmParameterDefineDto
 *  com.seeyon.bpm.dto.BpmParameterSettingDto
 */
package com.seeyon.bpm.api.udc;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmDataTypeDto;
import com.seeyon.bpm.dto.BpmParameterDataDto;
import com.seeyon.bpm.dto.BpmParameterDefineDto;
import com.seeyon.bpm.dto.BpmParameterSettingDto;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public interface BpmApiParamAppService {
    public SingleResponse<Void> saveParamSchema(SingleRequest<BpmParameterDefineDto> var1);

    public SingleResponse<Void> saveParamData(SingleRequest<BpmParameterDataDto> var1);

    public ListResponse<BpmParameterSettingDto> loadParamSchema(SingleRequest<Long> var1);

    public ListResponse<BpmDataTypeDto> loadParamTypes(SingleRequest<Void> var1);

    public SingleResponse<BpmParameterSettingDto> loadParamSchemaByOrigin(SingleRequest<String> var1);

    public SingleResponse<Void> deleteSettingByIds(SingleRequest<List<Long>> var1);

    default public ListResponse<BpmParameterSettingDto> selectParameterUsedByTemplateId(SingleRequest<Long> templateId) {
        return ListResponse.from(Collections.emptyList());
    }

    default public ListResponse<String> selectUsedParameterPathName(SingleRequest<Long> request) {
        return ListResponse.from(new ArrayList());
    }
}
