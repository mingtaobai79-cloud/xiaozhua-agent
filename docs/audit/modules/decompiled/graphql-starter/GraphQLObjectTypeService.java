/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.starter.graphql.GraphQLObjectTypeNReturnService
 *  com.seeyon.boot.starter.graphql.GraphQLObjectTypeParamsService
 *  com.seeyon.boot.starter.graphql.dto.DocDto
 *  com.seeyon.boot.starter.graphql.proxy.MetadataProxyService
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.ctp.metadata.dto.DtoMetadataDto
 *  com.seeyon.ctp.metadata.dto.EntityMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestApiMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestMethodMetadataDto
 *  graphql.schema.GraphQLFieldDefinition$Builder
 *  graphql.schema.GraphQLSchema$Builder
 *  org.dataloader.DataLoaderRegistry
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.context.annotation.Lazy
 *  org.springframework.stereotype.Component
 *  org.springframework.util.Assert
 *  org.springframework.util.CollectionUtils
 */
package com.seeyon.boot.starter.graphql;

import com.seeyon.boot.starter.graphql.GraphQLObjectTypeNReturnService;
import com.seeyon.boot.starter.graphql.GraphQLObjectTypeParamsService;
import com.seeyon.boot.starter.graphql.dto.DocDto;
import com.seeyon.boot.starter.graphql.proxy.MetadataProxyService;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.ctp.metadata.dto.DtoMetadataDto;
import com.seeyon.ctp.metadata.dto.EntityMetadataDto;
import com.seeyon.ctp.metadata.dto.RestApiMetadataDto;
import com.seeyon.ctp.metadata.dto.RestMethodMetadataDto;
import graphql.schema.GraphQLFieldDefinition;
import graphql.schema.GraphQLSchema;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.dataloader.DataLoaderRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;
import org.springframework.util.Assert;
import org.springframework.util.CollectionUtils;

@Component
public class GraphQLObjectTypeService {
    private static final Logger log = LoggerFactory.getLogger(GraphQLObjectTypeService.class);
    @Lazy
    @Autowired
    private MetadataProxyService metadataProxyService;
    @Autowired
    private GraphQLObjectTypeParamsService paramsService;
    @Autowired
    private GraphQLObjectTypeNReturnService nReturnService;
    public static Map<String, String> GRAPHQL_TYPE_MAPPING = new HashMap<String, String>();
    public static Map<String, List<DtoMetadataDto>> DTO_METADATA_DTO_CACHE = new HashMap<String, List<DtoMetadataDto>>();
    public static Map<String, List<EntityMetadataDto>> ENTITY_METADATA_DTO_CACHE = new HashMap<String, List<EntityMetadataDto>>();
    public static Map<String, List<RestApiMetadataDto>> REST_API_METADATA_DTO_CACHE = new HashMap<String, List<RestApiMetadataDto>>();
    private static Map<String, DataLoaderRegistry> DATA_LOADER_REGISTRY_CACHE = new HashMap<String, DataLoaderRegistry>();
    public static ThreadLocal<String> APP_CACHE = new ThreadLocal();
    public static Boolean autoFresh = false;
    private Map<String, Set<String>> restNameCache = new HashMap<String, Set<String>>();
    private Map<String, Set<String>> typeNameCache = new HashMap<String, Set<String>>();
    private static final Map<String, Set<String>> DATA_LOADER_CACHE = new HashMap<String, Set<String>>();

    public DataLoaderRegistry getRegistry(String appName) {
        if (null == DATA_LOADER_REGISTRY_CACHE.get(appName)) {
            DATA_LOADER_REGISTRY_CACHE.put(appName, new DataLoaderRegistry());
        }
        return DATA_LOADER_REGISTRY_CACHE.get(appName);
    }

    public void clearMetadataCache(String appName) {
        DTO_METADATA_DTO_CACHE.remove(appName);
        ENTITY_METADATA_DTO_CACHE.remove(appName);
        REST_API_METADATA_DTO_CACHE.remove(appName);
    }

    public void clearMetadataCache() {
        DTO_METADATA_DTO_CACHE.clear();
        ENTITY_METADATA_DTO_CACHE.clear();
        REST_API_METADATA_DTO_CACHE.clear();
    }

    public void addMethod(DocDto doc, GraphQLSchema.Builder baseBuilder, GraphQLFieldDefinition.Builder builder, RestMethodMetadataDto methodDto, String appName, String methodTypeName) throws Exception {
        if (this.uniqueRestCheck(methodTypeName, appName)) {
            Assert.isTrue((boolean)false, (String)("GraphQL初始化异常，出现重名Rest[" + methodTypeName + "]"));
        } else {
            this.restNameCacheAdd(methodTypeName, appName);
        }
        this.paramsService.addMethodParamList(doc, baseBuilder, builder, methodDto, appName, methodTypeName);
        this.nReturnService.addMethodReturn(baseBuilder, builder, methodDto, appName, methodTypeName);
    }

    public boolean uniqueRestCheck(String typeName, String appName) {
        Set cache = this.restNameCache.computeIfAbsent(appName, k -> new HashSet());
        return cache.contains(typeName);
    }

    public void restNameCacheAdd(String typeName, String appName) {
        Set cache = this.restNameCache.computeIfAbsent(appName, k -> new HashSet());
        cache.add(typeName);
    }

    public void clearRestNameCache(String appName) {
        this.restNameCache.remove(appName);
    }

    public boolean uniqueCheck(String typeName, String appName) {
        Set cache = this.typeNameCache.computeIfAbsent(appName, k -> new HashSet());
        return cache.contains(typeName);
    }

    public void typeNameCacheAdd(String typeName, String appName) {
        Set cache = this.typeNameCache.computeIfAbsent(appName, k -> new HashSet());
        cache.add(typeName);
    }

    public void clearTypeNameCache() {
        this.typeNameCache.clear();
    }

    public void clearDataloaderCache(String appName) {
        DATA_LOADER_CACHE.remove(appName);
    }

    public boolean dataloaderCached(String appName, String key) {
        if (null != DATA_LOADER_CACHE.get(appName)) {
            return DATA_LOADER_CACHE.get(appName).contains(key);
        }
        return false;
    }

    public void dataloaderCacheAdd(String appName, String key) {
        Set<String> cache = DATA_LOADER_CACHE.get(appName);
        if (null == cache) {
            cache = new HashSet<String>();
            DATA_LOADER_CACHE.put(appName, cache);
        }
        cache.add(key);
    }

    public void refreshDtoCache(String appName, ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse) {
        ListResponse restApiMetadata;
        ListResponse response = dtoMetadataDtoListResponse;
        if (null == response) {
            response = ListResponse.from((List)this.metadataProxyService.selectDtoMetadata(appName));
        }
        if (response.success()) {
            DTO_METADATA_DTO_CACHE.put(appName, response.getData().getContent());
        }
        if (null == (restApiMetadata = restApiMetadataDtoListResponse)) {
            restApiMetadata = ListResponse.from((List)this.metadataProxyService.selectRestApiMetadata(appName));
        }
        if (restApiMetadata.success()) {
            REST_API_METADATA_DTO_CACHE.put(appName, restApiMetadata.getData().getContent());
        }
        if (!CollectionUtils.isEmpty(ENTITY_METADATA_DTO_CACHE)) {
            ENTITY_METADATA_DTO_CACHE.clear();
        }
    }

    public void setAppCache(String appName) {
        APP_CACHE.set(appName);
    }

    public void clearAppCache() {
        APP_CACHE.remove();
    }

    public void clearCacheMapping() {
        GRAPHQL_TYPE_MAPPING.clear();
    }

    public void clearDataloaderRegistryCache(String appName) {
        DATA_LOADER_REGISTRY_CACHE.remove(appName);
    }
}
