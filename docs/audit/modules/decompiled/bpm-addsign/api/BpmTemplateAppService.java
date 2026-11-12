/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.common.Constants
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.AppDeleteDto
 *  com.seeyon.bpm.dto.BaseBpmHandlerParamDto
 *  com.seeyon.bpm.dto.BpmAppInfoDto
 *  com.seeyon.bpm.dto.BpmAppTemplateDto
 *  com.seeyon.bpm.dto.BpmNormalMultiVersionSearchDto
 *  com.seeyon.bpm.dto.BpmStartTemplateDto
 *  com.seeyon.bpm.dto.BpmTemplateAppSearchDto
 *  com.seeyon.bpm.dto.BpmTemplateAuthorizationDto
 *  com.seeyon.bpm.dto.BpmTemplateCategorySearchDto
 *  com.seeyon.bpm.dto.BpmTemplateDto
 *  com.seeyon.bpm.dto.BpmTemplateExtendUpdateDto
 *  com.seeyon.bpm.dto.BpmTemplateInfoDto
 *  com.seeyon.bpm.dto.BpmTemplateOwnerDto
 *  com.seeyon.bpm.dto.BpmTemplateParamDto
 *  com.seeyon.bpm.dto.BpmTemplateSimpleDto
 *  com.seeyon.bpm.dto.BpmTemplateUserGuidInfo
 *  com.seeyon.bpm.dto.BpmUpdateCategoryDto
 *  com.seeyon.bpm.dto.SeachTemplateInfoDto
 *  com.seeyon.bpm.dto.approval.BpmNodeDetailDto
 *  com.seeyon.bpm.dto.approval.BpmNodeDetailReqDto
 *  com.seeyon.bpm.dto.formtemplate.UserTemplateDto
 *  com.seeyon.bpm.dto.formtemplate.UserTemplateListRequestDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmTemplateOwnerSearchDto
 *  com.seeyon.bpm.dto.operation.openapi.BpmTemplateSearchConditionDto
 *  com.seeyon.bpm.dto.pathtable.BpmPathTableDefineBaseDto
 *  com.seeyon.bpm.dto.pathtable.BpmPathTableDefineSearchDto
 *  com.seeyon.bpm.dto.transport.BpmPublishResult
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.common.Constants;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.AppDeleteDto;
import com.seeyon.bpm.dto.BaseBpmHandlerParamDto;
import com.seeyon.bpm.dto.BpmAppInfoDto;
import com.seeyon.bpm.dto.BpmAppTemplateDto;
import com.seeyon.bpm.dto.BpmNormalMultiVersionSearchDto;
import com.seeyon.bpm.dto.BpmStartTemplateDto;
import com.seeyon.bpm.dto.BpmTemplateAppSearchDto;
import com.seeyon.bpm.dto.BpmTemplateAuthorizationDto;
import com.seeyon.bpm.dto.BpmTemplateCategorySearchDto;
import com.seeyon.bpm.dto.BpmTemplateDto;
import com.seeyon.bpm.dto.BpmTemplateExtendUpdateDto;
import com.seeyon.bpm.dto.BpmTemplateInfoDto;
import com.seeyon.bpm.dto.BpmTemplateOwnerDto;
import com.seeyon.bpm.dto.BpmTemplateParamDto;
import com.seeyon.bpm.dto.BpmTemplateSimpleDto;
import com.seeyon.bpm.dto.BpmTemplateUserGuidInfo;
import com.seeyon.bpm.dto.BpmUpdateCategoryDto;
import com.seeyon.bpm.dto.SeachTemplateInfoDto;
import com.seeyon.bpm.dto.approval.BpmNodeDetailDto;
import com.seeyon.bpm.dto.approval.BpmNodeDetailReqDto;
import com.seeyon.bpm.dto.formtemplate.UserTemplateDto;
import com.seeyon.bpm.dto.formtemplate.UserTemplateListRequestDto;
import com.seeyon.bpm.dto.operation.openapi.BpmTemplateOwnerSearchDto;
import com.seeyon.bpm.dto.operation.openapi.BpmTemplateSearchConditionDto;
import com.seeyon.bpm.dto.pathtable.BpmPathTableDefineBaseDto;
import com.seeyon.bpm.dto.pathtable.BpmPathTableDefineSearchDto;
import com.seeyon.bpm.dto.transport.BpmPublishResult;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Set;

public interface BpmTemplateAppService {
    public SingleResponse<Long> createOrUpdate(SingleRequest<BpmTemplateDto> var1);

    public SingleResponse<Void> deleteById(SingleRequest<Long> var1);

    public SingleResponse<Void> updateCategoryByApplicationId(SingleRequest<BpmUpdateCategoryDto> var1);

    @Deprecated
    public SingleResponse<Void> publishCheck(SingleRequest<String> var1);

    public SingleResponse<Void> publishCheckByAppInfo(SingleRequest<BpmAppInfoDto> var1);

    @Deprecated
    public SingleResponse<Void> publishLock(SingleRequest<String> var1);

    public SingleResponse<Void> publishLockByAppInfo(SingleRequest<BpmAppInfoDto> var1);

    public SingleResponse<Void> publishFinish(SingleRequest<BpmPublishResult> var1);

    public SingleResponse<Void> cleanCacheByApplicationName(SingleRequest<String> var1);

    public ListResponse<BpmTemplateDto> startCheck(SingleRequest<BpmStartTemplateDto> var1);

    @Deprecated
    public SingleResponse<Void> start(SingleRequest<String> var1, SingleRequest<String> var2);

    @Deprecated
    public ListResponse<BpmTemplateDto> startByTemplateId(SingleRequest<BpmStartTemplateDto> var1);

    @Deprecated
    public ListResponse<BpmTemplateDto> startByTemplateIdWithoutAuth(SingleRequest<BpmStartTemplateDto> var1);

    @Deprecated
    public SingleResponse<Void> stop(SingleRequest<String> var1);

    @Deprecated
    public SingleResponse<Void> stopByTemplateId(SingleRequest<Long> var1);

    public SingleResponse<Void> deleteByApps(SingleRequest<List<AppDeleteDto>> var1);

    public ListResponse<BpmTemplateDto> selectByApplicationName(SingleRequest<String> var1);

    @Deprecated
    public ListResponse<BpmTemplateDto> updateEffectTimeByTemplateId(SingleRequest<BpmStartTemplateDto> var1);

    @Deprecated
    public SingleResponse<Void> updateEffectTime(SingleRequest<String> var1, SingleRequest<Date> var2, SingleRequest<Date> var3);

    @Deprecated
    public SingleResponse<Void> updateAuthorized(SingleRequest<List<BpmTemplateAuthorizationDto>> var1);

    public SingleResponse<BpmTemplateDto> selectById(SingleRequest<Long> var1);

    default public ListResponse<BpmTemplateDto> selectTemplateListByCondition(SingleRequest<BpmTemplateSearchConditionDto> singleRequest) {
        return ListResponse.from(new ArrayList());
    }

    public SingleResponse<BpmTemplateSimpleDto> selectByTemplateUrlId(SingleRequest<Long> var1);

    public ListResponse<BpmAppTemplateDto> selectEffectedDiagramListByAppName(SingleRequest<BaseBpmHandlerParamDto> var1);

    public ListResponse<BpmTemplateUserGuidInfo> selectTemplateUserGuidInfo(SingleRequest<Long> var1);

    @Deprecated
    public SingleResponse<BpmTemplateInfoDto> selectTemplateById(SingleRequest<SeachTemplateInfoDto> var1);

    default public PageResponse<BpmPathTableDefineBaseDto> selectPathTableCondition(SingleRequest<BpmPathTableDefineSearchDto> searchDtoSingleRequest) {
        return null;
    }

    public ListResponse<Long> selectTemplateIdsByName(SingleRequest<String> var1);

    public ListResponse<BpmTemplateDto> selectTemplateByRootEntityId(SingleRequest<Long> var1);

    public SingleResponse<BpmTemplateDto> selectTemplateByParams(SingleRequest<BpmTemplateParamDto> var1);

    default public ListResponse<BpmTemplateDto> selectTemplateByRootEntityName(SingleRequest<String> request) {
        return null;
    }

    default public SingleResponse<Boolean> hasDesignTemplateByEntityName(SingleRequest<String> entityName) {
        return null;
    }

    default public ListResponse<BpmTemplateDto> selectByIds(SingleRequest<List<Long>> request) {
        return ListResponse.from(new ArrayList());
    }

    public PageResponse<UserTemplateDto> selectUserTemplatePageList(SingleRequest<UserTemplateListRequestDto> var1);

    public ListResponse<Long> selectTemplateGuidByCategoryCode(SingleRequest<String> var1);

    default public PageResponse<BpmTemplateOwnerDto> selectBpmTemplateOwnerPageList(SingleRequest<BpmTemplateOwnerSearchDto> request) {
        return null;
    }

    default public ListResponse<String> filterEnableTemplateAppName(SingleRequest<List<String>> applicationName) {
        return ListResponse.from((List)((List)applicationName.getData()));
    }

    default public SingleResponse<BpmTemplateDto> selectCascadeById(SingleRequest<Long> request) {
        return null;
    }

    default public ListResponse<BpmTemplateDto> selectCascadeByIds(SingleRequest<List<Long>> request) {
        return null;
    }

    default public PageResponse<BpmTemplateDto> dynamicSelect(SingleRequest<ProxyParamDto> request) {
        return null;
    }

    public SingleResponse<Integer> updateByAppName(SingleRequest<BpmTemplateDto> var1);

    default public PageResponse<BpmTemplateDto> dynamicJoinSelect(SingleRequest<ProxyJoinParamDto> request) {
        return null;
    }

    default public SingleResponse<BpmTemplateDto> selectCascadeByConditions(SingleRequest<QueryConditionDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<BpmTemplateDto> selectCascadeListByConditions(SingleRequest<QueryConditionDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public ListResponse<Long> selectTemplateIdListByGuid(SingleRequest<Long> request) {
        return null;
    }

    public SingleResponse<BpmNodeDetailDto> selectNodeDetail(SingleRequest<BpmNodeDetailReqDto> var1);

    default public SingleResponse<BpmTemplateDto> selectByIdDisplayName(SingleRequest<Long> id, SingleRequest<Set<String>> fieldSet) {
        return SingleResponse.from((Object)new BpmTemplateDto());
    }

    default public ListResponse<BpmTemplateDto> selectByIdsDisplayName(SingleRequest<List<Long>> ids, SingleRequest<Set<String>> fieldSet) {
        return ListResponse.from(new ArrayList());
    }

    default public ListResponse<Long> selectTemplateBySearchDto(SingleRequest<BpmTemplateAppSearchDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public ListResponse<Long> selectTemplateByCategoryIds(SingleRequest<BpmTemplateCategorySearchDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<Long> updateTemplateExtend(SingleRequest<BpmTemplateExtendUpdateDto> request) {
        return SingleResponse.from((Object)Constants.LONG_ZERO);
    }

    default public ListResponse<BpmTemplateDto> selectNormalMultiVersionDraft(SingleRequest<BpmNormalMultiVersionSearchDto> request) {
        return ListResponse.from(new ArrayList());
    }

    default public SingleResponse<BpmTemplateDto> getCascadeDefaultValue(SingleRequest<Void> request) {
        return SingleResponse.from((Object)new BpmTemplateDto());
    }

    default public SingleResponse<BpmTemplateDto> getCascadeDefaultValue() {
        return SingleResponse.from((Object)new BpmTemplateDto());
    }

    default public ListResponse<BpmTemplateDto> selectLatestTemplateByGuids(SingleRequest<List<Long>> request) {
        return ListResponse.from(new ArrayList());
    }
}
