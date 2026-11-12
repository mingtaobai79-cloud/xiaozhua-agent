/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.context.SystemEnvironment
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.util.StringUtils
 *  com.seeyon.ctp.metadata.domain.service.MetadataService
 *  com.seeyon.ctp.metadata.dto.AppServiceMetadataDto
 *  com.seeyon.ctp.metadata.dto.DtoMetadataDto
 *  com.seeyon.ctp.metadata.dto.EntityMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestApiMetadataDto
 *  com.seeyon.ctp.metadata.dto.ServiceMetadataDto
 *  com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto
 *  com.seeyon.ctp.metadata.dto.request.SearchMetadataDto
 *  com.seeyon.ctp.metadata.enums.MetadataTypeEnum
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.context.annotation.Lazy
 *  org.springframework.stereotype.Component
 *  org.springframework.util.CollectionUtils
 */
package com.seeyon.boot.starter.graphql.proxy;

import com.seeyon.boot.context.Apps;
import com.seeyon.boot.context.SystemEnvironment;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.ctp.metadata.domain.service.MetadataService;
import com.seeyon.ctp.metadata.dto.AppServiceMetadataDto;
import com.seeyon.ctp.metadata.dto.DtoMetadataDto;
import com.seeyon.ctp.metadata.dto.EntityMetadataDto;
import com.seeyon.ctp.metadata.dto.RestApiMetadataDto;
import com.seeyon.ctp.metadata.dto.ServiceMetadataDto;
import com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto;
import com.seeyon.ctp.metadata.dto.request.SearchMetadataDto;
import com.seeyon.ctp.metadata.enums.MetadataTypeEnum;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;

@Component
public class MetadataProxyService {
    public static List<DtoMetadataDto> DTO_METADATA_DTO_CACHE = new ArrayList<DtoMetadataDto>();
    public static List<EntityMetadataDto> ENTITY_METADATA_DTO_CACHE = new ArrayList<EntityMetadataDto>();
    public static List<RestApiMetadataDto> REST_API_METADATA_DTO_CACHE = new ArrayList<RestApiMetadataDto>();
    public static ServiceMetadataDto SERVICE_METADATA_DTO_CACHE = null;
    @Lazy
    @Autowired
    private MetadataService metadataService;

    public void clearCache() {
        DTO_METADATA_DTO_CACHE.clear();
        ENTITY_METADATA_DTO_CACHE.clear();
        REST_API_METADATA_DTO_CACHE.clear();
    }

    public void setCache(ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse, ListResponse<EntityMetadataDto> entityMetadataDtoListResponse, SingleResponse<ServiceMetadataDto> serviceMetadataDtoSingleResponse) {
        if (restApiMetadataDtoListResponse.success()) {
            REST_API_METADATA_DTO_CACHE = restApiMetadataDtoListResponse.getData().getContent();
        }
        if (dtoMetadataDtoListResponse.success()) {
            DTO_METADATA_DTO_CACHE = dtoMetadataDtoListResponse.getData().getContent();
        }
        if (entityMetadataDtoListResponse.success()) {
            ENTITY_METADATA_DTO_CACHE = entityMetadataDtoListResponse.getData().getContent();
        }
        if (serviceMetadataDtoSingleResponse.success()) {
            SERVICE_METADATA_DTO_CACHE = (ServiceMetadataDto)serviceMetadataDtoSingleResponse.getData().getContent();
        }
    }

    public List<RestApiMetadataDto> selectRestApiMetadata(String appName) {
        if (SystemEnvironment.isGray() && Apps.getAppName().equals(appName) && !CollectionUtils.isEmpty(REST_API_METADATA_DTO_CACHE)) {
            return REST_API_METADATA_DTO_CACHE;
        }
        SearchMetadataDto searchMetadataDto = new SearchMetadataDto();
        searchMetadataDto.setAppName(appName);
        Map map = this.metadataService.selectForMap(MetadataTypeEnum.RestApi, searchMetadataDto);
        if (!CollectionUtils.isEmpty((Map)map)) {
            return new ArrayList<RestApiMetadataDto>(map.values());
        }
        return REST_API_METADATA_DTO_CACHE;
    }

    public List<DtoMetadataDto> selectDtoMetadata(String appName) {
        if (SystemEnvironment.isGray() && Apps.getAppName().equals(appName) && !CollectionUtils.isEmpty(DTO_METADATA_DTO_CACHE)) {
            return DTO_METADATA_DTO_CACHE;
        }
        SearchMetadataDto searchMetadataDto = new SearchMetadataDto();
        searchMetadataDto.setAppName(appName);
        Map map = this.metadataService.selectForMap(MetadataTypeEnum.Dto, searchMetadataDto);
        if (!CollectionUtils.isEmpty((Map)map)) {
            return new ArrayList<DtoMetadataDto>(map.values());
        }
        return DTO_METADATA_DTO_CACHE;
    }

    public List<EntityMetadataDto> selectEntityMetadata(String appName) {
        if (SystemEnvironment.isGray() && Apps.getAppName().equals(appName) && !CollectionUtils.isEmpty(ENTITY_METADATA_DTO_CACHE)) {
            return ENTITY_METADATA_DTO_CACHE;
        }
        SearchMetadataDto searchMetadataDto = new SearchMetadataDto();
        searchMetadataDto.setAppName(appName);
        Map map = this.metadataService.selectForMap(MetadataTypeEnum.Entity, searchMetadataDto);
        if (!CollectionUtils.isEmpty((Map)map)) {
            return new ArrayList<EntityMetadataDto>(map.values());
        }
        return ENTITY_METADATA_DTO_CACHE;
    }

    public ServiceMetadataDto selectServiceMetadataByName(String appName) {
        if (SystemEnvironment.isGray() && Apps.getAppName().equals(appName) && null != SERVICE_METADATA_DTO_CACHE) {
            return SERVICE_METADATA_DTO_CACHE;
        }
        ServiceMetadataDto serviceMetadataDto = this.metadataService.selectServiceMetadataByName(appName);
        if (serviceMetadataDto != null) {
            return serviceMetadataDto;
        }
        return SERVICE_METADATA_DTO_CACHE;
    }

    public DtoMetadataDto selectDtoMetadataByFullName(String appName, String dtoFullName) {
        if (SystemEnvironment.isGray() && Apps.getAppName().equals(appName) && !CollectionUtils.isEmpty(DTO_METADATA_DTO_CACHE)) {
            for (DtoMetadataDto dtoMetadataDto : DTO_METADATA_DTO_CACHE) {
                if (!dtoFullName.equals(dtoMetadataDto.getType())) continue;
                return dtoMetadataDto;
            }
        }
        SearchByFullNameDto searchMetadataDto = new SearchByFullNameDto();
        searchMetadataDto.setAppName(appName);
        searchMetadataDto.setFullName(dtoFullName);
        return (DtoMetadataDto)this.metadataService.selectByFullName(MetadataTypeEnum.Dto, searchMetadataDto);
    }

    public AppServiceMetadataDto selectAppServiceMetadataByEntityFullName(String appName, String entityFullName) {
        SearchMetadataDto searchMetadataDto = new SearchMetadataDto();
        searchMetadataDto.setAppName(appName);
        Map map = this.metadataService.selectForMap(MetadataTypeEnum.AppService, searchMetadataDto);
        if (!CollectionUtils.isEmpty((Map)map)) {
            ArrayList appServiceMetadataDtoList = new ArrayList(map.values());
            Optional<AppServiceMetadataDto> optional = appServiceMetadataDtoList.stream().filter(x -> !CollectionUtils.isEmpty((Map)x.getCustoms())).filter(x -> Objects.nonNull(x.getCustoms().get("entity"))).filter(x -> x.getCustoms().get("entity").equals(entityFullName)).findFirst();
            if (optional.isPresent()) {
                return optional.get();
            }
            optional = appServiceMetadataDtoList.stream().filter(x -> {
                String entityName;
                String appServiceName = StringUtils.substringAfterLast((String)x.getFullName(), (String)".");
                return appServiceName.equals((entityName = StringUtils.substringAfterLast((String)entityFullName, (String)".")) + "AppService") || appServiceName.equals(entityName + "AppServiceImpl");
            }).findFirst();
            if (optional.isPresent()) {
                return optional.get();
            }
        }
        throw new RuntimeException("应用" + appName + "的实体" + entityFullName + "无法识别其AppService信息");
    }
}
