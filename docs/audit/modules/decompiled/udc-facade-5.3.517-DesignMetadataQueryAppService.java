/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.ctp.metadata.dto.AggEntityMetadataDto
 *  com.seeyon.ctp.metadata.dto.AggMetadataDto
 *  com.seeyon.ctp.metadata.dto.AppServiceMetadataDto
 *  com.seeyon.ctp.metadata.dto.DtoMetadataDto
 *  com.seeyon.ctp.metadata.dto.EntityMetadataDto
 *  com.seeyon.ctp.metadata.dto.EnumMetadataDto
 *  com.seeyon.ctp.metadata.dto.MqMetadataDto
 *  com.seeyon.ctp.metadata.dto.OpenApiMetadataDto
 *  com.seeyon.ctp.metadata.dto.PageMetadataDto
 *  com.seeyon.ctp.metadata.dto.ReferAndAppMetadataDto
 *  com.seeyon.ctp.metadata.dto.ReferMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestApiMetadataDto
 *  com.seeyon.ctp.metadata.dto.ServiceMetadataDto
 *  com.seeyon.udc.dto.meta.SearchDesignMetadataByFullNameDto
 *  com.seeyon.udc.dto.meta.SearchDesignMetadataByFullNamesDto
 *  com.seeyon.udc.dto.meta.SearchDesignMetadataDto
 *  com.seeyon.udc.dto.meta.UdcAppMetaDataQueryDto
 */
package com.seeyon.udc.api;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.ctp.metadata.dto.AggEntityMetadataDto;
import com.seeyon.ctp.metadata.dto.AggMetadataDto;
import com.seeyon.ctp.metadata.dto.AppServiceMetadataDto;
import com.seeyon.ctp.metadata.dto.DtoMetadataDto;
import com.seeyon.ctp.metadata.dto.EntityMetadataDto;
import com.seeyon.ctp.metadata.dto.EnumMetadataDto;
import com.seeyon.ctp.metadata.dto.MqMetadataDto;
import com.seeyon.ctp.metadata.dto.OpenApiMetadataDto;
import com.seeyon.ctp.metadata.dto.PageMetadataDto;
import com.seeyon.ctp.metadata.dto.ReferAndAppMetadataDto;
import com.seeyon.ctp.metadata.dto.ReferMetadataDto;
import com.seeyon.ctp.metadata.dto.RestApiMetadataDto;
import com.seeyon.ctp.metadata.dto.ServiceMetadataDto;
import com.seeyon.udc.dto.meta.SearchDesignMetadataByFullNameDto;
import com.seeyon.udc.dto.meta.SearchDesignMetadataByFullNamesDto;
import com.seeyon.udc.dto.meta.SearchDesignMetadataDto;
import com.seeyon.udc.dto.meta.UdcAppMetaDataQueryDto;
import java.util.List;

public interface DesignMetadataQueryAppService {
    public SingleResponse<ServiceMetadataDto> selectServiceMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<EntityMetadataDto> selectEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<EntityMetadataDto> selectEntityMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public SingleResponse<EntityMetadataDto> selectEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<EntityMetadataDto> selectEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public ListResponse<AggMetadataDto> selectAggMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<AggMetadataDto> selectAggMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public SingleResponse<AggMetadataDto> selectAggMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<AggMetadataDto> selectAggMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public ListResponse<EntityMetadataDto> selectEntityListByAgg(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<RestApiMetadataDto> selectRestApiMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<RestApiMetadataDto> selectRestApiMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<RestApiMetadataDto> selectRestApiMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<RestApiMetadataDto> selectRestApiMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<DtoMetadataDto> selectDtoMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<DtoMetadataDto> selectDtoMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<DtoMetadataDto> selectDtoMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<DtoMetadataDto> selectDtoMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<EnumMetadataDto> selectEnumMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<EnumMetadataDto> selectEnumMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<EnumMetadataDto> selectEnumMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<AggEntityMetadataDto> selectAggEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataByCondition(SingleRequest<UdcAppMetaDataQueryDto> var1);

    public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public SingleResponse<AggEntityMetadataDto> selectAggEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public ListResponse<OpenApiMetadataDto> selectOpenApiMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<OpenApiMetadataDto> selectOpenApiMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<OpenApiMetadataDto> selectOpenApiMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<AppServiceMetadataDto> selectAppServiceMetadata(SingleRequest<String> var1);

    public ListResponse<AppServiceMetadataDto> selectAppServiceMetadataExcludeBoot(SingleRequest<String> var1);

    public ListResponse<AppServiceMetadataDto> selectAppServiceMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<AppServiceMetadataDto> selectAppServiceMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<MqMetadataDto> selectMqMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<MqMetadataDto> selectMqMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<MqMetadataDto> selectMqMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<MqMetadataDto> selectMqMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<DtoMetadataDto> selectEntityRelationDtoMetadata(SingleRequest<String> var1);

    public ListResponse<DtoMetadataDto> selectEntityRelationDtoMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<DtoMetadataDto> selectDtoMetadataByEntityFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public SingleResponse<DtoMetadataDto> selectDtoMetadataByEntityFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public SingleResponse<AppServiceMetadataDto> selectAppServiceMetadataByDto(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<ReferMetadataDto> selectReferMetadataByEntity(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public SingleResponse<ReferAndAppMetadataDto> selectReferAndAppMetadataByEntity(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<EntityMetadataDto> selectBasicDataEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);

    public SingleResponse<EntityMetadataDto> selectBasicDataEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);

    public ListResponse<EntityMetadataDto> selectBasicDataEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);

    public ListResponse<PageMetadataDto> selectPageMetadataList(SingleRequest<SearchDesignMetadataDto> var1);

    public ListResponse<EnumMetadataDto> selectEnumMetadataList(SingleRequest<List<Long>> var1);
}
