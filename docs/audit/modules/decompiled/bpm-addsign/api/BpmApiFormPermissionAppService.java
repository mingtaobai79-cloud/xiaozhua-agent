/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmFormDesensitizedDto
 *  com.seeyon.bpm.dto.BpmFormDesensitizedQueryDto
 *  com.seeyon.bpm.dto.BpmFormPermissionContentDto
 *  com.seeyon.bpm.dto.BpmFormPermissionContentSimpleDto
 *  com.seeyon.bpm.dto.BpmFormPermissionDeleteRequestDto
 *  com.seeyon.bpm.dto.BpmFormPermissionDto
 *  com.seeyon.bpm.dto.BpmFormPermissionIncludeContentDto
 *  com.seeyon.bpm.dto.BpmFormPermissionSearchRequestDto
 *  com.seeyon.bpm.dto.CheckFormPermissionRespDto
 *  com.seeyon.bpm.dto.ThirdFormPermissionDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmFormDesensitizedDto;
import com.seeyon.bpm.dto.BpmFormDesensitizedQueryDto;
import com.seeyon.bpm.dto.BpmFormPermissionContentDto;
import com.seeyon.bpm.dto.BpmFormPermissionContentSimpleDto;
import com.seeyon.bpm.dto.BpmFormPermissionDeleteRequestDto;
import com.seeyon.bpm.dto.BpmFormPermissionDto;
import com.seeyon.bpm.dto.BpmFormPermissionIncludeContentDto;
import com.seeyon.bpm.dto.BpmFormPermissionSearchRequestDto;
import com.seeyon.bpm.dto.CheckFormPermissionRespDto;
import com.seeyon.bpm.dto.ThirdFormPermissionDto;
import java.util.ArrayList;
import java.util.List;

public interface BpmApiFormPermissionAppService {
    public SingleResponse<Long> create(SingleRequest<BpmFormPermissionDto> var1);

    public SingleResponse<Void> update(SingleRequest<BpmFormPermissionDto> var1);

    public SingleResponse<Void> deleteById(SingleRequest<Long> var1);

    public ListResponse<BpmFormPermissionDto> selectByTemplateId(SingleRequest<Long> var1);

    public SingleResponse<BpmFormPermissionDto> selectById(SingleRequest<Long> var1);

    public SingleResponse<BpmFormPermissionIncludeContentDto> selectPermissionIncludeContentById(SingleRequest<Long> var1);

    public ListResponse<BpmFormPermissionDto> selectByApplicationName(SingleRequest<String> var1);

    default public SingleResponse<ThirdFormPermissionDto> selectThirdPermissionByTemplateId(SingleRequest<Long> templateId) {
        return null;
    }

    public ListResponse<BpmFormPermissionDto> selectByIds(SingleRequest<List<Long>> var1);

    default public ListResponse<BpmFormDesensitizedDto> selectFormDesensitizedList(SingleRequest<BpmFormDesensitizedQueryDto> request) {
        return null;
    }

    default public SingleResponse<ThirdFormPermissionDto> selectThirdFormPermissionById(SingleRequest<Long> id) {
        return SingleResponse.from((Object)new ThirdFormPermissionDto());
    }

    default public ListResponse<BpmFormPermissionDto> selectFormPermissionList(SingleRequest<BpmFormPermissionSearchRequestDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Void> deleteFormPermisionForceEntityDraft(SingleRequest<BpmFormPermissionDeleteRequestDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmFormPermissionIncludeContentDto> selectFormPermissionIncludeContentList(SingleRequest<List<BpmFormPermissionSearchRequestDto>> request) {
        return ListResponse.from(new ArrayList());
    }

    public SingleResponse<Void> createOrUpdateBatch(SingleRequest<List<BpmFormPermissionDto>> var1);

    public SingleResponse<Void> createBatchOrUpdateContent(SingleRequest<List<BpmFormPermissionContentDto>> var1);

    public ListResponse<BpmFormPermissionContentSimpleDto> selectContentListByPermissionIds(SingleRequest<List<Long>> var1);

    public ListResponse<CheckFormPermissionRespDto> checkFormPermissionBatch(SingleRequest<List<BpmFormPermissionDto>> var1);
}
