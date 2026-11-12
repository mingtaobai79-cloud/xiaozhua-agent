/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.starter.graphql.GraphQLObjectTypeService
 *  com.seeyon.boot.starter.graphql.dto.DocDto
 *  com.seeyon.boot.starter.graphql.dto.DocExtensionsDto
 *  com.seeyon.boot.starter.graphql.proxy.MetadataProxyService
 *  com.seeyon.boot.starter.graphql.util.GraphQLTypeMappingUtil
 *  com.seeyon.boot.starter.graphql.util.GraphQLTypeNameUtil
 *  com.seeyon.boot.starter.graphql.util.SeeyonScalars
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.util.StringUtils
 *  com.seeyon.ctp.metadata.dto.DtoAttributeMetadataDto
 *  com.seeyon.ctp.metadata.dto.DtoMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestMethodMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestParamMetadataDto
 *  graphql.Scalars
 *  graphql.schema.GraphQLArgument
 *  graphql.schema.GraphQLEnumType
 *  graphql.schema.GraphQLEnumType$Builder
 *  graphql.schema.GraphQLFieldDefinition$Builder
 *  graphql.schema.GraphQLInputObjectField
 *  graphql.schema.GraphQLInputObjectType
 *  graphql.schema.GraphQLInputObjectType$Builder
 *  graphql.schema.GraphQLInputType
 *  graphql.schema.GraphQLList
 *  graphql.schema.GraphQLSchema$Builder
 *  graphql.schema.GraphQLType
 *  graphql.schema.GraphQLTypeReference
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.context.annotation.Lazy
 *  org.springframework.stereotype.Component
 *  org.springframework.util.Assert
 *  org.springframework.util.CollectionUtils
 */
package com.seeyon.boot.starter.graphql;

import com.seeyon.boot.starter.graphql.GraphQLObjectTypeService;
import com.seeyon.boot.starter.graphql.dto.DocDto;
import com.seeyon.boot.starter.graphql.dto.DocExtensionsDto;
import com.seeyon.boot.starter.graphql.proxy.MetadataProxyService;
import com.seeyon.boot.starter.graphql.util.GraphQLTypeMappingUtil;
import com.seeyon.boot.starter.graphql.util.GraphQLTypeNameUtil;
import com.seeyon.boot.starter.graphql.util.SeeyonScalars;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.ctp.metadata.dto.DtoAttributeMetadataDto;
import com.seeyon.ctp.metadata.dto.DtoMetadataDto;
import com.seeyon.ctp.metadata.dto.RestMethodMetadataDto;
import com.seeyon.ctp.metadata.dto.RestParamMetadataDto;
import graphql.Scalars;
import graphql.schema.GraphQLArgument;
import graphql.schema.GraphQLEnumType;
import graphql.schema.GraphQLFieldDefinition;
import graphql.schema.GraphQLInputObjectField;
import graphql.schema.GraphQLInputObjectType;
import graphql.schema.GraphQLInputType;
import graphql.schema.GraphQLList;
import graphql.schema.GraphQLSchema;
import graphql.schema.GraphQLType;
import graphql.schema.GraphQLTypeReference;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;
import org.springframework.util.Assert;
import org.springframework.util.CollectionUtils;

@Component
public class GraphQLObjectTypeParamsService {
    private static final Logger log = LoggerFactory.getLogger(GraphQLObjectTypeParamsService.class);
    public static final String BODY = "body";
    public static final String QUERY = "query";
    @Lazy
    @Autowired
    private MetadataProxyService metadataProxyService;
    @Autowired
    private GraphQLObjectTypeService typeService;

    /*
     * WARNING - void declaration
     */
    public void addMethodParamList(DocDto doc, GraphQLSchema.Builder baseBuilder, GraphQLFieldDefinition.Builder builder, RestMethodMetadataDto methodDto, String appName, String methodTypeName) throws Exception {
        doc.setName(methodTypeName);
        doc.setSdl("");
        doc.setDescription(methodDto.getCaption() == null ? methodDto.getDescription() : methodDto.getCaption());
        DocExtensionsDto extensions = new DocExtensionsDto();
        doc.setExtensions(extensions);
        extensions.setAppName(appName);
        extensions.setUrl(methodDto.getPath().replaceAll("//", "/"));
        extensions.setMethod(methodDto.getHttpMethod());
        extensions.setGraphqlKey(methodTypeName);
        List paramList = methodDto.getParamList();
        HashMap<String, String> pathParams = new HashMap<String, String>();
        HashMap<String, RestParamMetadataDto> queryParams = new HashMap<String, RestParamMetadataDto>();
        HashMap<String, RestParamMetadataDto> bodyParams = new HashMap<String, RestParamMetadataDto>();
        if (!CollectionUtils.isEmpty((Collection)paramList)) {
            for (RestParamMetadataDto param : paramList) {
                if ("path".equals(param.getParamType())) {
                    extensions.setType("path");
                    pathParams.put(param.getName(), param.getType());
                    continue;
                }
                if (BODY.equals(param.getParamType())) {
                    extensions.setType(BODY);
                    bodyParams.put(param.getName(), param);
                    continue;
                }
                if ("form".equals(param.getParamType()) || "formData".equals(param.getParamType())) {
                    log.error("暂不支持form,formData请求参数类型,PATH[{}]", (Object)methodDto.getPath());
                    throw new Exception("暂不支持form,formData请求参数类型");
                }
                extensions.setType(QUERY);
                queryParams.put(param.getName(), param);
            }
        } else {
            extensions.setType(QUERY);
        }
        if (!CollectionUtils.isEmpty(bodyParams)) {
            Object paramMetadataDto;
            String bodyTypeName = methodTypeName + "InputBody";
            GraphQLInputObjectType.Builder bodyType = GraphQLInputObjectType.newInputObject().name(bodyTypeName);
            boolean requestBody = false;
            for (Map.Entry entry : bodyParams.entrySet()) {
                paramMetadataDto = (RestParamMetadataDto)entry.getValue();
                if (!"RequestBody".equals(paramMetadataDto.getBodyType())) continue;
                requestBody = true;
                break;
            }
            if (requestBody) {
                GraphQLEnumType enumType;
                GraphQLEnumType.Builder enumBuilder;
                String enumTypeName;
                Object attributes;
                RestParamMetadataDto paramMetadataDto2 = (RestParamMetadataDto)bodyParams.entrySet().iterator().next().getValue();
                String string = paramMetadataDto2.getType();
                if (string.startsWith("com.") && CollectionUtils.isEmpty((Collection)paramMetadataDto2.getEnums())) {
                    for (DtoMetadataDto dtoMetadataDto : (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName)) {
                        if (!string.equals(dtoMetadataDto.getType())) continue;
                        bodyType.field(GraphQLInputObjectField.newInputObjectField().name("validate").description("校验标识").type((GraphQLInputType)Scalars.GraphQLBoolean));
                        attributes = dtoMetadataDto.getAttributes();
                        if (CollectionUtils.isEmpty((Map)attributes)) continue;
                        this.handleQueryField(baseBuilder, bodyType, (Map<String, DtoAttributeMetadataDto>)attributes, appName);
                    }
                    baseBuilder.additionalType((GraphQLType)bodyType.build());
                    builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)new GraphQLTypeReference(bodyTypeName)));
                } else if ("java.util.List".equals(string) || "java.util.Set".equals(string) || string.endsWith("[]")) {
                    void var16_21;
                    if (string.endsWith("[]")) {
                        String string2 = string.substring(0, string.length() - 2);
                    } else {
                        String string3 = paramMetadataDto2.getItem().getItemType();
                    }
                    if (var16_21.startsWith("com.") && (null == paramMetadataDto2.getItem() || CollectionUtils.isEmpty((Collection)paramMetadataDto2.getItem().getEnums()))) {
                        for (DtoMetadataDto dtoMetadataDto : (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName)) {
                            if (!var16_21.equals(dtoMetadataDto.getType())) continue;
                            bodyType.field(GraphQLInputObjectField.newInputObjectField().name("validate").description("校验标识").type((GraphQLInputType)Scalars.GraphQLBoolean));
                            attributes = dtoMetadataDto.getAttributes();
                            if (CollectionUtils.isEmpty((Map)attributes)) continue;
                            this.handleQueryField(baseBuilder, bodyType, (Map<String, DtoAttributeMetadataDto>)attributes, appName);
                        }
                        baseBuilder.additionalType((GraphQLType)bodyType.build());
                        builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(bodyTypeName))));
                    } else if (null != paramMetadataDto2.getItem() && !CollectionUtils.isEmpty((Collection)paramMetadataDto2.getItem().getEnums())) {
                        enumTypeName = this.getTypeCacheMapping((String)var16_21, true);
                        if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                            enumTypeName = GraphQLTypeNameUtil.touchName((String)var16_21, (String)appName, (boolean)true);
                            enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                            for (String item : paramMetadataDto2.getItem().getEnums()) {
                                enumBuilder.value(item);
                            }
                            enumType = enumBuilder.build();
                            baseBuilder.additionalType((GraphQLType)enumType);
                            this.setTypeCacheMapping((String)var16_21, enumTypeName, true);
                        }
                        builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(enumTypeName))));
                    } else {
                        builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)GraphQLList.list((GraphQLType)GraphQLTypeMappingUtil.get((String)var16_21))));
                    }
                } else if (!CollectionUtils.isEmpty((Collection)paramMetadataDto2.getEnums())) {
                    enumTypeName = this.getTypeCacheMapping(string, true);
                    if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                        enumTypeName = GraphQLTypeNameUtil.touchName((String)string, (String)appName, (boolean)true);
                        enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                        for (String item : paramMetadataDto2.getEnums()) {
                            enumBuilder.value(item);
                        }
                        enumType = enumBuilder.build();
                        baseBuilder.additionalType((GraphQLType)enumType);
                        this.setTypeCacheMapping(string, enumTypeName, true);
                    }
                    builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)new GraphQLTypeReference(enumTypeName)));
                } else {
                    builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)GraphQLTypeMappingUtil.get((String)string)));
                }
            } else {
                for (Map.Entry entry : bodyParams.entrySet()) {
                    paramMetadataDto = (RestParamMetadataDto)entry.getValue();
                    this.handleQuery(baseBuilder, bodyType, (RestParamMetadataDto)paramMetadataDto, appName, BODY);
                }
                baseBuilder.additionalType((GraphQLType)bodyType.build());
                builder.argument(GraphQLArgument.newArgument().name(BODY).type((GraphQLInputType)new GraphQLTypeReference(bodyTypeName)));
            }
        }
        if (!CollectionUtils.isEmpty(pathParams)) {
            String pathTypeName = methodTypeName + "InputPath";
            GraphQLInputObjectType.Builder pathType = GraphQLInputObjectType.newInputObject().name(pathTypeName);
            pathParams.forEach((k, v) -> pathType.field(GraphQLInputObjectField.newInputObjectField().name(k).type((GraphQLInputType)GraphQLTypeMappingUtil.get((String)v))));
            baseBuilder.additionalType((GraphQLType)pathType.build());
            builder.argument(GraphQLArgument.newArgument().name("path").type((GraphQLInputType)new GraphQLTypeReference(pathTypeName)));
        }
        if (!CollectionUtils.isEmpty(queryParams)) {
            String queryTypeName = methodTypeName + "InputQuery";
            GraphQLInputObjectType.Builder quryType = GraphQLInputObjectType.newInputObject().name(queryTypeName);
            for (Map.Entry entry : queryParams.entrySet()) {
                this.handleQuery(baseBuilder, quryType, (RestParamMetadataDto)entry.getValue(), appName, QUERY);
            }
            baseBuilder.additionalType((GraphQLType)quryType.build());
            builder.argument(GraphQLArgument.newArgument().name(QUERY).type((GraphQLInputType)new GraphQLTypeReference(queryTypeName)));
        }
    }

    private void handleQuery(GraphQLSchema.Builder baseBuilder, GraphQLInputObjectType.Builder queryType, RestParamMetadataDto paramMetadataDto, String appName, String type) throws Exception {
        String paramType = paramMetadataDto.getType();
        if (paramType.startsWith("com.") && CollectionUtils.isEmpty((Collection)paramMetadataDto.getEnums())) {
            if (QUERY.equals(type)) {
                for (DtoMetadataDto dtoMetadataDto : (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName)) {
                    Map attributes;
                    if (!paramType.equals(dtoMetadataDto.getType()) || CollectionUtils.isEmpty((Map)(attributes = dtoMetadataDto.getAttributes()))) continue;
                    this.handleQueryField(baseBuilder, queryType, attributes, appName);
                }
            } else {
                String paramDtoType = this.getParamDtoType(baseBuilder, appName, paramType, true);
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).type((GraphQLInputType)new GraphQLTypeReference(paramDtoType)));
            }
        } else if ("java.util.List".equals(paramType) || "java.util.Set".equals(paramType) || paramType.endsWith("[]")) {
            if ((paramType = paramType.endsWith("[]") ? paramType.substring(0, paramType.length() - 2) : paramMetadataDto.getItem().getItemType()).startsWith("com.") && (null == paramMetadataDto.getItem() || CollectionUtils.isEmpty((Collection)paramMetadataDto.getItem().getEnums()))) {
                String paramDtoType = this.getParamDtoType(baseBuilder, appName, paramType, true);
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(paramDtoType))));
            } else if (paramMetadataDto.getItem() != null && !CollectionUtils.isEmpty((Collection)paramMetadataDto.getItem().getEnums())) {
                String enumTypeName = this.getTypeCacheMapping(paramType, true);
                if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                    enumTypeName = GraphQLTypeNameUtil.touchName((String)paramType, (String)appName, (boolean)true);
                    GraphQLEnumType.Builder enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                    for (String item : paramMetadataDto.getItem().getEnums()) {
                        enumBuilder.value(item);
                    }
                    GraphQLEnumType enumType = enumBuilder.build();
                    baseBuilder.additionalType((GraphQLType)enumType);
                    this.setTypeCacheMapping(paramType, enumTypeName, true);
                }
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).description(paramMetadataDto.getCaption()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(enumTypeName))));
            } else {
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).description(paramMetadataDto.getCaption()).type((GraphQLInputType)GraphQLList.list((GraphQLType)GraphQLTypeMappingUtil.get((String)paramType))));
            }
        } else if (!CollectionUtils.isEmpty((Collection)paramMetadataDto.getEnums())) {
            String enumTypeName = this.getTypeCacheMapping(paramType, true);
            if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                enumTypeName = GraphQLTypeNameUtil.touchName((String)paramType, (String)appName, (boolean)true);
                GraphQLEnumType.Builder enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                for (String item : paramMetadataDto.getEnums()) {
                    enumBuilder.value(item);
                }
                GraphQLEnumType enumType = enumBuilder.build();
                baseBuilder.additionalType((GraphQLType)enumType);
                this.setTypeCacheMapping(paramType, enumTypeName, true);
            }
            queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).description(paramMetadataDto.getCaption()).type((GraphQLInputType)new GraphQLTypeReference(enumTypeName)));
        } else {
            queryType.field(GraphQLInputObjectField.newInputObjectField().name(paramMetadataDto.getName()).description(paramMetadataDto.getCaption()).type((GraphQLInputType)GraphQLTypeMappingUtil.get((String)paramType)));
        }
    }

    private void handleQueryField(GraphQLSchema.Builder baseBuilder, GraphQLInputObjectType.Builder queryType, Map<String, DtoAttributeMetadataDto> attributes, String appName) throws Exception {
        for (Map.Entry<String, DtoAttributeMetadataDto> entry : attributes.entrySet()) {
            GraphQLEnumType enumType;
            GraphQLEnumType.Builder enumBuilder;
            String enumTypeName;
            DtoAttributeMetadataDto dtoAttributeMetadataDto = entry.getValue();
            String fieldName = entry.getKey();
            String fieldType = dtoAttributeMetadataDto.getType();
            if (fieldType.startsWith("com.") && CollectionUtils.isEmpty((Collection)dtoAttributeMetadataDto.getEnums())) {
                String res = this.getAttributeDtoMapping(baseBuilder, appName, dtoAttributeMetadataDto, (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName), true);
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)new GraphQLTypeReference(res)));
                continue;
            }
            if ("java.util.List".equals(fieldType) || "java.util.Set".equals(fieldType) || fieldType.endsWith("[]")) {
                if ((fieldType = fieldType.endsWith("[]") ? fieldType.substring(0, fieldType.length() - 2) : dtoAttributeMetadataDto.getItem().getItemType()).startsWith("com.") && (null == dtoAttributeMetadataDto.getItem() || CollectionUtils.isEmpty((Collection)dtoAttributeMetadataDto.getItem().getEnums()))) {
                    String dtoMapping = this.getAttributeDtoMappingForList(baseBuilder, appName, dtoAttributeMetadataDto, (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName), true);
                    queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(dtoMapping))));
                    continue;
                }
                if (null != dtoAttributeMetadataDto.getItem() && !CollectionUtils.isEmpty((Collection)dtoAttributeMetadataDto.getItem().getEnums())) {
                    enumTypeName = this.getTypeCacheMapping(fieldType, true);
                    if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                        enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)true);
                        enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                        for (String item : dtoAttributeMetadataDto.getItem().getEnums()) {
                            enumBuilder.value(item);
                        }
                        enumType = enumBuilder.build();
                        baseBuilder.additionalType((GraphQLType)enumType);
                        this.setTypeCacheMapping(fieldType, enumTypeName, true);
                    }
                    queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(enumTypeName))));
                    continue;
                }
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)GraphQLTypeMappingUtil.get((String)fieldType))));
                continue;
            }
            if (!CollectionUtils.isEmpty((Collection)dtoAttributeMetadataDto.getEnums())) {
                enumTypeName = this.getTypeCacheMapping(fieldType, true);
                if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                    enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)true);
                    enumBuilder = GraphQLEnumType.newEnum().name(enumTypeName);
                    for (String item : dtoAttributeMetadataDto.getEnums()) {
                        enumBuilder.value(item);
                    }
                    enumType = enumBuilder.build();
                    baseBuilder.additionalType((GraphQLType)enumType);
                    this.setTypeCacheMapping(fieldType, enumTypeName, true);
                }
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)new GraphQLTypeReference(enumTypeName)));
                continue;
            }
            if (dtoAttributeMetadataDto.isXssProcess() && "java.lang.String".equals(dtoAttributeMetadataDto.getType())) {
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)SeeyonScalars.GRAPHQL_SCALAR_TYPE));
            } else {
                queryType.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(dtoAttributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLTypeMappingUtil.get((String)fieldType)));
            }
            this.childrenMock(queryType, dtoAttributeMetadataDto, fieldName);
        }
    }

    private String getAttributeDtoMapping(GraphQLSchema.Builder baseBuilder, String appName, DtoAttributeMetadataDto attributeMetadataDto, List<DtoMetadataDto> dtoMetadataDtos, boolean isInput) throws Exception {
        String fieldType = attributeMetadataDto.getType();
        String res = this.getTypeCacheMapping(fieldType, isInput);
        if (StringUtils.isEmpty((CharSequence)res)) {
            if (!CollectionUtils.isEmpty((Collection)attributeMetadataDto.getEnums())) {
                String enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)isInput);
                GraphQLEnumType.Builder builder = GraphQLEnumType.newEnum().name(enumTypeName);
                for (String item : attributeMetadataDto.getEnums()) {
                    builder.value(item);
                }
                baseBuilder.additionalType((GraphQLType)builder.build());
                this.setTypeCacheMapping(fieldType, enumTypeName, isInput);
            } else if (!StringUtils.isEmpty((CharSequence)attributeMetadataDto.getRefApp()) && !appName.equals(attributeMetadataDto.getRefApp())) {
                String refApp = attributeMetadataDto.getRefApp();
                List dtoMetadataDtoList = (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(refApp);
                if (CollectionUtils.isEmpty((Collection)dtoMetadataDtoList)) {
                    ListResponse response = ListResponse.from((List)this.metadataProxyService.selectDtoMetadata(refApp));
                    dtoMetadataDtoList = response.getData().getContent();
                    GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.put(refApp, dtoMetadataDtoList);
                }
                this.scanDtoByFullName(baseBuilder, fieldType, refApp, dtoMetadataDtoList);
            } else {
                this.scanDtoByFullName(baseBuilder, fieldType, appName, dtoMetadataDtos);
            }
            res = this.getTypeCacheMapping(fieldType, isInput);
        }
        if (StringUtils.isEmpty((CharSequence)res)) {
            log.error(fieldType + "在元数据不存在，无法转换为GraphQL Schema");
            throw new Exception(fieldType + "在元数据不存在，无法转换为GraphQL Schema");
        }
        return res;
    }

    private String getAttributeDtoMappingForList(GraphQLSchema.Builder baseBuilder, String appName, DtoAttributeMetadataDto attributeMetadataDto, List<DtoMetadataDto> dtoMetadataDtos, boolean isInput) throws Exception {
        String fieldType = attributeMetadataDto.getItem().getItemType();
        String res = this.getTypeCacheMapping(fieldType, isInput);
        if (StringUtils.isEmpty((CharSequence)res)) {
            if (!CollectionUtils.isEmpty((Collection)attributeMetadataDto.getItem().getEnums())) {
                String enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)isInput);
                GraphQLEnumType.Builder builder = GraphQLEnumType.newEnum().name(enumTypeName);
                for (String item : attributeMetadataDto.getItem().getEnums()) {
                    builder.value(item);
                }
                baseBuilder.additionalType((GraphQLType)builder.build());
                this.setTypeCacheMapping(fieldType, enumTypeName, isInput);
            } else if (!StringUtils.isEmpty((CharSequence)attributeMetadataDto.getRefApp()) && !appName.equals(attributeMetadataDto.getRefApp())) {
                String refApp = attributeMetadataDto.getRefApp();
                List dtoMetadataDtoList = (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(refApp);
                if (CollectionUtils.isEmpty((Collection)dtoMetadataDtoList)) {
                    ListResponse response = ListResponse.from((List)this.metadataProxyService.selectDtoMetadata(refApp));
                    dtoMetadataDtoList = response.getData().getContent();
                    GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.put(refApp, dtoMetadataDtoList);
                }
                this.scanDtoByFullName(baseBuilder, fieldType, refApp, dtoMetadataDtoList);
            } else {
                this.scanDtoByFullName(baseBuilder, fieldType, appName, dtoMetadataDtos);
            }
            res = this.getTypeCacheMapping(fieldType, isInput);
        }
        if (StringUtils.isEmpty((CharSequence)res)) {
            log.error(fieldType + "在元数据不存在，无法转换为GraphQL Schema");
            throw new Exception(fieldType + "在元数据不存在，无法转换为GraphQL Schema");
        }
        return res;
    }

    private String getParamDtoType(GraphQLSchema.Builder baseBuilder, String appName, String paramType, boolean isInput) throws Exception {
        String graphgQLType = this.getTypeCacheMapping(paramType, isInput);
        if (StringUtils.isEmpty((CharSequence)graphgQLType)) {
            for (DtoMetadataDto dtoMetadataDto : (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName)) {
                if (!paramType.equals(dtoMetadataDto.getType())) continue;
                this.createDtoType(baseBuilder, dtoMetadataDto, (List)GraphQLObjectTypeService.DTO_METADATA_DTO_CACHE.get(appName), appName);
            }
            graphgQLType = this.getTypeCacheMapping(paramType, isInput);
        }
        if (StringUtils.isEmpty((CharSequence)graphgQLType)) {
            log.error(paramType + "在元数据不存在,无法转换为GraphQL Schema Type");
            throw new Exception(paramType + "在元数据不存在,无法转换为GraphQL Schema Type");
        }
        return graphgQLType;
    }

    private void scanDtoByFullName(GraphQLSchema.Builder baseBuilder, String fullName, String appName, List<DtoMetadataDto> dtoMetadataDtos) throws Exception {
        for (DtoMetadataDto dtoMetadataDto : dtoMetadataDtos) {
            if (!fullName.equals(dtoMetadataDto.getType())) continue;
            this.createDtoType(baseBuilder, dtoMetadataDto, dtoMetadataDtos, appName);
        }
    }

    public void createDtoType(GraphQLSchema.Builder baseBuilder, DtoMetadataDto metadataDto, List<DtoMetadataDto> dtoMetadataDtos, String appName) throws Exception {
        if (this.isCacheMapping(metadataDto.getFullName(), true)) {
            return;
        }
        String typeName = GraphQLTypeNameUtil.touchName((String)metadataDto.getFullName(), (String)appName, (boolean)true);
        if (this.typeService.uniqueCheck(typeName, appName)) {
            Assert.isTrue((boolean)false, (String)("GraphQL初始化异常，出现重名Dto[" + metadataDto.getFullName() + "]"));
        } else {
            this.typeService.typeNameCacheAdd(typeName, appName);
        }
        this.setTypeCacheMapping(metadataDto.getFullName(), typeName, true);
        GraphQLInputObjectType.Builder dtoTypeBuilder = GraphQLInputObjectType.newInputObject().name(typeName);
        try {
            Map properties = metadataDto.getAttributes();
            dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name("validate").description("校验标识").type((GraphQLInputType)Scalars.GraphQLBoolean));
            if (!properties.isEmpty()) {
                for (Map.Entry entry : properties.entrySet()) {
                    GraphQLEnumType.Builder builder;
                    String enumTypeName;
                    DtoAttributeMetadataDto attributeMetadataDto = (DtoAttributeMetadataDto)entry.getValue();
                    String fieldName = (String)entry.getKey();
                    String fieldType = attributeMetadataDto.getType();
                    if (fieldName.endsWith("___displayname")) continue;
                    if (fieldType.startsWith("com.") && CollectionUtils.isEmpty((Collection)attributeMetadataDto.getEnums())) {
                        String res = this.getAttributeDtoMapping(baseBuilder, appName, attributeMetadataDto, dtoMetadataDtos, true);
                        dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)new GraphQLTypeReference(res)));
                        continue;
                    }
                    if ("java.util.List".equals(fieldType) || "java.util.Set".equals(fieldType) || fieldType.endsWith("[]")) {
                        if ((fieldType = fieldType.endsWith("[]") ? fieldType.substring(0, fieldType.length() - 2) : attributeMetadataDto.getItem().getItemType()).startsWith("com.") && (null == attributeMetadataDto.getItem() || CollectionUtils.isEmpty((Collection)attributeMetadataDto.getItem().getEnums()))) {
                            String mapping = this.getAttributeDtoMappingForList(baseBuilder, appName, attributeMetadataDto, dtoMetadataDtos, true);
                            dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(mapping))));
                            continue;
                        }
                        if (null != attributeMetadataDto.getItem() && !CollectionUtils.isEmpty((Collection)attributeMetadataDto.getItem().getEnums())) {
                            enumTypeName = this.getTypeCacheMapping(fieldType, true);
                            if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                                enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)true);
                                builder = GraphQLEnumType.newEnum().name(enumTypeName);
                                for (String item : attributeMetadataDto.getItem().getEnums()) {
                                    builder.value(item);
                                }
                                baseBuilder.additionalType((GraphQLType)builder.build());
                                this.setTypeCacheMapping(fieldType, enumTypeName, true);
                            }
                            dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)new GraphQLTypeReference(enumTypeName))));
                            continue;
                        }
                        dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLList.list((GraphQLType)GraphQLTypeMappingUtil.get((String)fieldType))));
                        continue;
                    }
                    if (!CollectionUtils.isEmpty((Collection)attributeMetadataDto.getEnums())) {
                        enumTypeName = this.getTypeCacheMapping(fieldType, true);
                        if (StringUtils.isEmpty((CharSequence)enumTypeName)) {
                            enumTypeName = GraphQLTypeNameUtil.touchName((String)fieldType, (String)appName, (boolean)true);
                            builder = GraphQLEnumType.newEnum().name(enumTypeName);
                            for (String item : attributeMetadataDto.getEnums()) {
                                builder.value(item);
                            }
                            baseBuilder.additionalType((GraphQLType)builder.build());
                            this.setTypeCacheMapping(fieldType, enumTypeName, true);
                        }
                        dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)new GraphQLTypeReference(enumTypeName)));
                        continue;
                    }
                    if (attributeMetadataDto.isXssProcess() && "java.lang.String".equals(attributeMetadataDto.getType())) {
                        dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)SeeyonScalars.GRAPHQL_SCALAR_TYPE));
                    } else {
                        dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(fieldName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)GraphQLTypeMappingUtil.get((String)fieldType)));
                    }
                    this.childrenMock(dtoTypeBuilder, attributeMetadataDto, fieldName);
                }
            }
        }
        catch (Exception e) {
            this.removeTypeCacheMapping(metadataDto.getFullName(), false);
            log.error("{}生成GraphQL_Type[{}]异常:{}", new Object[]{metadataDto.getFullName(), typeName, e.getMessage()});
            throw e;
        }
        this.setTypeCacheMapping(metadataDto.getFullName(), typeName, true);
        baseBuilder.additionalType((GraphQLType)dtoTypeBuilder.build());
    }

    private void childrenMock(GraphQLInputObjectType.Builder dtoTypeBuilder, DtoAttributeMetadataDto attributeMetadataDto, String fieldName) {
        if (!StringUtils.isEmpty((CharSequence)attributeMetadataDto.getRef())) {
            String refName = fieldName + "___displayname";
            dtoTypeBuilder.field(GraphQLInputObjectField.newInputObjectField().name(refName).description(attributeMetadataDto.getDescription()).type((GraphQLInputType)SeeyonScalars.GRAPHQL_OBJECT));
        }
    }

    private boolean isCacheMapping(String key, boolean isInput) {
        String res;
        if (isInput) {
            key = key + "InputBody";
        }
        return !StringUtils.isEmpty((CharSequence)(res = (String)GraphQLObjectTypeService.GRAPHQL_TYPE_MAPPING.get(key)));
    }

    private void setTypeCacheMapping(String key, String graphQLTypeName, boolean isInput) {
        if (isInput) {
            key = key + "InputBody";
        }
        GraphQLObjectTypeService.GRAPHQL_TYPE_MAPPING.put(key, graphQLTypeName);
    }

    private void removeTypeCacheMapping(String key, boolean isInput) {
        if (isInput) {
            key = key + "InputBody";
        }
        GraphQLObjectTypeService.GRAPHQL_TYPE_MAPPING.remove(key);
    }

    private String getTypeCacheMapping(String key, boolean isInput) {
        if (isInput) {
            key = key + "InputBody";
        }
        return (String)GraphQLObjectTypeService.GRAPHQL_TYPE_MAPPING.get(key);
    }
}
