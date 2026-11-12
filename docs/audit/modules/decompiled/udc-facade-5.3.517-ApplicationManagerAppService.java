/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.udc.common.constant.UdcCommonConstant
 *  com.seeyon.udc.common.dto.AppInfoExportDto
 *  com.seeyon.udc.common.dto.AppVersionDto
 *  com.seeyon.udc.common.dto.ApplicationCopyDto
 *  com.seeyon.udc.common.dto.ApplicationDto
 *  com.seeyon.udc.common.dto.ApplicationExportDto
 *  com.seeyon.udc.common.dto.ApplicationImportDto
 *  com.seeyon.udc.common.dto.AttributeGroupDto
 *  com.seeyon.udc.common.dto.DependentApplicationDto
 *  com.seeyon.udc.common.dto.DeployFerryDto
 *  com.seeyon.udc.common.dto.DeployFormDto
 *  com.seeyon.udc.common.dto.DeployNormalDto
 *  com.seeyon.udc.common.dto.DeployParamDto
 *  com.seeyon.udc.common.dto.DeployRecordDto
 *  com.seeyon.udc.common.dto.DeployResultDto
 *  com.seeyon.udc.common.dto.EntityDto
 *  com.seeyon.udc.common.dto.ImportValidationInfo
 *  com.seeyon.udc.dto.app.ApplicationSearchDto
 *  com.seeyon.udc.dto.app.BaseApplicationSearchDto
 *  com.seeyon.udc.dto.form.CreateOnlyPageApplicationDto
 *  com.seeyon.udc.dto.form.IntegrationApplicationDto
 *  com.seeyon.udc.dto.form.LayoutApplicationDto
 *  com.seeyon.udc.dto.form.NewLayoutCreateAfterCallDto
 *  com.seeyon.udc.dto.form.OnlyPageApplicationDto
 *  com.seeyon.udc.dto.form.OnlyPageApplicationUpgradeDto
 *  com.seeyon.udc.dto.form.OnlyPageApplicationUpgradeResultDto
 *  com.seeyon.udc.dto.form.QueryFormInfoDto
 *  com.seeyon.udc.dto.member.AppCategoryDto
 *  com.seeyon.udc.dto.member.AppCollaborationDto
 *  com.seeyon.udc.dto.member.AppHanoverDto
 *  com.seeyon.udc.dto.member.ApplicationWithMemberDto
 *  com.seeyon.udc.dto.member.MemberAddDto
 *  com.seeyon.udc.dto.shelf.ShelfCompatibilityLockRequestDto
 *  com.seeyon.udc.dto.shelf.ShelfCompatibilityLockResultDto
 *  com.seeyon.udc.dto.shelf.ShelfDependRequestDto
 *  com.seeyon.udc.dto.shelf.ShelfDependResponseDto
 *  org.apache.commons.compress.utils.Lists
 */
package com.seeyon.udc.api;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.udc.common.constant.UdcCommonConstant;
import com.seeyon.udc.common.dto.AppInfoExportDto;
import com.seeyon.udc.common.dto.AppVersionDto;
import com.seeyon.udc.common.dto.ApplicationCopyDto;
import com.seeyon.udc.common.dto.ApplicationDto;
import com.seeyon.udc.common.dto.ApplicationExportDto;
import com.seeyon.udc.common.dto.ApplicationImportDto;
import com.seeyon.udc.common.dto.AttributeGroupDto;
import com.seeyon.udc.common.dto.DependentApplicationDto;
import com.seeyon.udc.common.dto.DeployFerryDto;
import com.seeyon.udc.common.dto.DeployFormDto;
import com.seeyon.udc.common.dto.DeployNormalDto;
import com.seeyon.udc.common.dto.DeployParamDto;
import com.seeyon.udc.common.dto.DeployRecordDto;
import com.seeyon.udc.common.dto.DeployResultDto;
import com.seeyon.udc.common.dto.EntityDto;
import com.seeyon.udc.common.dto.ImportValidationInfo;
import com.seeyon.udc.dto.app.ApplicationSearchDto;
import com.seeyon.udc.dto.app.BaseApplicationSearchDto;
import com.seeyon.udc.dto.form.CreateOnlyPageApplicationDto;
import com.seeyon.udc.dto.form.IntegrationApplicationDto;
import com.seeyon.udc.dto.form.LayoutApplicationDto;
import com.seeyon.udc.dto.form.NewLayoutCreateAfterCallDto;
import com.seeyon.udc.dto.form.OnlyPageApplicationDto;
import com.seeyon.udc.dto.form.OnlyPageApplicationUpgradeDto;
import com.seeyon.udc.dto.form.OnlyPageApplicationUpgradeResultDto;
import com.seeyon.udc.dto.form.QueryFormInfoDto;
import com.seeyon.udc.dto.member.AppCategoryDto;
import com.seeyon.udc.dto.member.AppCollaborationDto;
import com.seeyon.udc.dto.member.AppHanoverDto;
import com.seeyon.udc.dto.member.ApplicationWithMemberDto;
import com.seeyon.udc.dto.member.MemberAddDto;
import com.seeyon.udc.dto.shelf.ShelfCompatibilityLockRequestDto;
import com.seeyon.udc.dto.shelf.ShelfCompatibilityLockResultDto;
import com.seeyon.udc.dto.shelf.ShelfDependRequestDto;
import com.seeyon.udc.dto.shelf.ShelfDependResponseDto;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.apache.commons.compress.utils.Lists;

public interface ApplicationManagerAppService {
    public SingleResponse<Long> create(SingleRequest<ApplicationDto> var1);

    public ListResponse<OnlyPageApplicationDto> createOnlyPageApplication(SingleRequest<CreateOnlyPageApplicationDto> var1);

    public SingleResponse<Void> createNewLayoutAfterCall(SingleRequest<NewLayoutCreateAfterCallDto> var1);

    public SingleResponse<OnlyPageApplicationDto> copyOnlyPageApp(SingleRequest<ApplicationCopyDto> var1);

    public SingleResponse<OnlyPageApplicationUpgradeResultDto> upgradeOnlyPageApplication(SingleRequest<OnlyPageApplicationUpgradeDto> var1);

    public SingleResponse<IntegrationApplicationDto> createIntegrationApplication(SingleRequest<IntegrationApplicationDto> var1);

    public SingleResponse<LayoutApplicationDto> createLayoutApplication(SingleRequest<LayoutApplicationDto> var1);

    public SingleResponse<LayoutApplicationDto> copyLayoutApp(SingleRequest<ApplicationCopyDto> var1);

    public SingleResponse<ApplicationDto> selectById(SingleRequest<Long> var1);

    public SingleResponse<Integer> update(SingleRequest<ApplicationDto> var1);

    public SingleResponse<Integer> updateWithMember(SingleRequest<ApplicationWithMemberDto> var1);

    public SingleResponse<Integer> updateAppCategoryBatch(SingleRequest<AppCategoryDto> var1);

    public SingleResponse<Integer> deleteById(SingleRequest<Long> var1);

    public SingleResponse<ApplicationDto> copyApp(SingleRequest<ApplicationCopyDto> var1);

    public SingleResponse<String> copyAppAsync(SingleRequest<ApplicationCopyDto> var1);

    public SingleResponse<Integer> createMember(SingleRequest<MemberAddDto> var1);

    public ListResponse<AppCollaborationDto> selectCollaborationRecordsByAppId(SingleRequest<Long> var1);

    public SingleResponse<Void> deleteMemberById(SingleRequest<Long> var1);

    default public SingleResponse<Integer> handoverApp(SingleRequest<AppHanoverDto> appHanoverDto) {
        return SingleResponse.from((Object)0);
    }

    public SingleResponse<ApplicationDto> createReturnDto(SingleRequest<ApplicationDto> var1);

    public SingleResponse<Integer> deleteFormAppByGuid(SingleRequest<Long> var1);

    public SingleResponse<Integer> deleteFormAppByName(SingleRequest<String> var1);

    public SingleResponse<DeployParamDto> deployNormal(SingleRequest<DeployNormalDto> var1);

    public SingleResponse<DeployResultDto> deployForm(SingleRequest<DeployFormDto> var1);

    public SingleResponse<ApplicationDto> selectLatestDesignAppByGuid(SingleRequest<Long> var1);

    public SingleResponse<ApplicationWithMemberDto> selectLatestDesignAppWithMemberByGuid(SingleRequest<Long> var1);

    public SingleResponse<Map<String, Long>> selectAppNameAndIdMapByAppNames(SingleRequest<List<String>> var1);

    public ListResponse<ApplicationDto> selectDesignAppByGuid(SingleRequest<Long> var1);

    public PageResponse<ApplicationDto> selectAppByUser(SingleRequest<ApplicationSearchDto> var1);

    public ListResponse<ApplicationDto> selectAppByUserAndGuid(SingleRequest<ApplicationSearchDto> var1);

    public SingleResponse<ApplicationDto> selectAppByUserAndId(SingleRequest<ApplicationSearchDto> var1);

    public ListResponse<ApplicationExportDto> exportAppInfos(SingleRequest<AppInfoExportDto> var1);

    public SingleResponse<AppVersionDto> selectAppDeployState(SingleRequest<QueryFormInfoDto> var1);

    default public SingleResponse<String> downloadApp(SingleRequest<Long> request) {
        return SingleResponse.from((Object)"");
    }

    default public SingleResponse<String> downloadAppAsync(SingleRequest<Long> request) {
        return SingleResponse.from((Object)"");
    }

    default public SingleResponse<String> downloadAppByHost(SingleRequest<Long> request) {
        return SingleResponse.from((Object)"");
    }

    default public SingleResponse<Long> importApp(SingleRequest<String> request) {
        return SingleResponse.from((Object)UdcCommonConstant.NULL_ID);
    }

    default public SingleResponse<Long> importAppWithDto(SingleRequest<ApplicationImportDto> request) {
        return SingleResponse.from((Object)UdcCommonConstant.NULL_ID);
    }

    default public SingleResponse<String> batchDownloadAppAsync(SingleRequest<List<Long>> request) {
        return SingleResponse.from((Object)"");
    }

    default public SingleResponse<String> batchTransferAppAsync(SingleRequest<List<String>> request, SingleRequest<Map<String, Object>> params) {
        return SingleResponse.from((Object)"");
    }

    default public ListResponse<ImportValidationInfo> importFormValidate(String storageKey, ApplicationCopyDto applicationCopyDto) {
        return ListResponse.from(null);
    }

    default public SingleResponse<String> importFormApp(String storageKey, ApplicationCopyDto applicationCopyDto) {
        return SingleResponse.from((Object)"requestId");
    }

    default public SingleResponse<Long> transfer(SingleRequest<String> request) throws IOException {
        return SingleResponse.from((Object)UdcCommonConstant.NULL_ID);
    }

    default public SingleResponse<Long> transfer(SingleRequest<String> request, SingleRequest<Map<String, Object>> params) throws IOException {
        return SingleResponse.from((Object)UdcCommonConstant.NULL_ID);
    }

    default public SingleResponse<ShelfDependResponseDto> getShelfDepend(SingleRequest<ShelfDependRequestDto> request) {
        return SingleResponse.from(null);
    }

    default public ListResponse<DependentApplicationDto> getDependsByAppId(SingleRequest<Long> request) {
        return ListResponse.from(Collections.emptyList());
    }

    default public ListResponse<DependentApplicationDto> getDependsLayoutAppInfo(SingleRequest<BaseApplicationSearchDto> request) {
        return ListResponse.from(Collections.emptyList());
    }

    default public SingleResponse<ShelfCompatibilityLockResultDto> shelfCompatibilityLock(SingleRequest<ShelfCompatibilityLockRequestDto> request) {
        return SingleResponse.ok();
    }

    default public SingleResponse<Long> migrationApp(SingleRequest<DeployFerryDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<DeployRecordDto> selectDeployRecordById(SingleRequest<Long> request) {
        return ListResponse.from(Collections.emptyList());
    }

    public PageResponse<ApplicationDto> selectAppPageByConditions(PageRequest var1);

    default public SingleResponse<Long> createEntity(SingleRequest<EntityDto> request) {
        return SingleResponse.ok();
    }

    default public ListResponse<AttributeGroupDto> operateBatch(SingleRequest<List<AttributeGroupDto>> attributeGroupDtoList) {
        return ListResponse.from((List)Lists.newArrayList());
    }
}
