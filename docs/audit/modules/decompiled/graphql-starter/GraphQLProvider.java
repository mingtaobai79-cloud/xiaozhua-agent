/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.starter.graphql.AppHostService
 *  com.seeyon.boot.starter.graphql.GraphQLObjectTypeService
 *  com.seeyon.boot.starter.graphql.dto.DocDto
 *  com.seeyon.boot.starter.graphql.execution.SeeyonRest
 *  com.seeyon.boot.starter.graphql.execution.SeeyonSchema
 *  com.seeyon.boot.starter.graphql.execution.SeeyonSchemaService
 *  com.seeyon.boot.starter.graphql.proxy.MetadataProxyService
 *  com.seeyon.boot.starter.graphql.util.DynamicDataServletFetcher
 *  com.seeyon.boot.starter.graphql.util.SeeyonThreadPool
 *  com.seeyon.boot.starter.graphql.util.ThreadLocalUtil
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.util.DateUtils
 *  com.seeyon.ctp.metadata.dto.DtoMetadataDto
 *  com.seeyon.ctp.metadata.dto.EntityMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestApiMetadataDto
 *  com.seeyon.ctp.metadata.dto.RestMethodMetadataDto
 *  com.seeyon.ctp.metadata.dto.ServiceMetadataDto
 *  graphql.GraphQL
 *  graphql.Scalars
 *  graphql.execution.instrumentation.Instrumentation
 *  graphql.execution.instrumentation.dataloader.DataLoaderDispatcherInstrumentation
 *  graphql.execution.instrumentation.dataloader.DataLoaderDispatcherInstrumentationOptions
 *  graphql.schema.DataFetcher
 *  graphql.schema.GraphQLFieldDefinition
 *  graphql.schema.GraphQLFieldDefinition$Builder
 *  graphql.schema.GraphQLObjectType
 *  graphql.schema.GraphQLObjectType$Builder
 *  graphql.schema.GraphQLOutputType
 *  graphql.schema.GraphQLSchema
 *  graphql.schema.GraphQLSchema$Builder
 *  org.apache.commons.lang3.StringUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.context.annotation.Lazy
 *  org.springframework.stereotype.Component
 *  org.springframework.util.CollectionUtils
 */
package com.seeyon.boot.starter.graphql;

import com.seeyon.boot.context.Apps;
import com.seeyon.boot.starter.graphql.AppHostService;
import com.seeyon.boot.starter.graphql.GraphQLObjectTypeService;
import com.seeyon.boot.starter.graphql.dto.DocDto;
import com.seeyon.boot.starter.graphql.execution.SeeyonRest;
import com.seeyon.boot.starter.graphql.execution.SeeyonSchema;
import com.seeyon.boot.starter.graphql.execution.SeeyonSchemaService;
import com.seeyon.boot.starter.graphql.proxy.MetadataProxyService;
import com.seeyon.boot.starter.graphql.util.DynamicDataServletFetcher;
import com.seeyon.boot.starter.graphql.util.SeeyonThreadPool;
import com.seeyon.boot.starter.graphql.util.ThreadLocalUtil;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.util.DateUtils;
import com.seeyon.ctp.metadata.dto.DtoMetadataDto;
import com.seeyon.ctp.metadata.dto.EntityMetadataDto;
import com.seeyon.ctp.metadata.dto.RestApiMetadataDto;
import com.seeyon.ctp.metadata.dto.RestMethodMetadataDto;
import com.seeyon.ctp.metadata.dto.ServiceMetadataDto;
import graphql.GraphQL;
import graphql.Scalars;
import graphql.execution.instrumentation.Instrumentation;
import graphql.execution.instrumentation.dataloader.DataLoaderDispatcherInstrumentation;
import graphql.execution.instrumentation.dataloader.DataLoaderDispatcherInstrumentationOptions;
import graphql.schema.DataFetcher;
import graphql.schema.GraphQLFieldDefinition;
import graphql.schema.GraphQLObjectType;
import graphql.schema.GraphQLOutputType;
import graphql.schema.GraphQLSchema;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;

@Component
public class GraphQLProvider {
    private static final Logger log = LoggerFactory.getLogger(GraphQLProvider.class);
    private static Map<String, GraphQL> graphQLMap = new HashMap<String, GraphQL>();
    @Autowired(required=false)
    private GraphQLObjectTypeService graphQLObjectTypeService;
    @Autowired
    private AppHostService hostService;
    @Autowired
    private SeeyonThreadPool pool;
    @Autowired
    private SeeyonSchemaService schemaCache;
    @Lazy
    @Autowired
    private MetadataProxyService metadataProxyService;
    private static Map<String, List<DocDto>> docCache = new HashMap<String, List<DocDto>>();

    public GraphQL graphQL() {
        return graphQLMap.get(Apps.getAppName());
    }

    public GraphQL graphQL(String appName) {
        return graphQLMap.get(appName);
    }

    public void run(ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse) {
        String appName = Apps.getAppName();
        log.error("GraphQL 初始化开始.");
        long s = System.currentTimeMillis();
        this.hostService.addApp(appName);
        this.loadMetaData(appName, restApiMetadataDtoListResponse, dtoMetadataDtoListResponse);
        log.error("GraphQL 初始化结束[{}ms].", (Object)(System.currentTimeMillis() - s));
    }

    public void run(ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse, ListResponse<EntityMetadataDto> entityMetadataDtoListResponse, SingleResponse<ServiceMetadataDto> serviceMetadataDtoSingleResponse) {
        String appName = Apps.getAppName();
        this.metadataProxyService.setCache(restApiMetadataDtoListResponse, dtoMetadataDtoListResponse, entityMetadataDtoListResponse, serviceMetadataDtoSingleResponse);
        log.error("GraphQL 初始化开始.");
        long s = System.currentTimeMillis();
        this.hostService.addApp(appName);
        this.loadMetaData(appName, restApiMetadataDtoListResponse, dtoMetadataDtoListResponse);
        log.error("GraphQL 初始化结束[{}ms].", (Object)(System.currentTimeMillis() - s));
    }

    public void run(String appName, ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse) {
        log.info("应用[{}]GraphQL 初始化开始.", (Object)appName);
        long s = System.currentTimeMillis();
        this.hostService.addApp(appName);
        this.loadMetaData(appName, restApiMetadataDtoListResponse, dtoMetadataDtoListResponse);
        log.info("应用[{}]GraphQL 初始化结束[{}ms].", (Object)appName, (Object)(System.currentTimeMillis() - s));
    }

    public void run(String appName, ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse, ListResponse<EntityMetadataDto> entityMetadataDtoListResponse, SingleResponse<ServiceMetadataDto> serviceMetadataDtoSingleResponse) {
        log.info("应用[{}]GraphQL 初始化开始.", (Object)appName);
        if (Apps.getAppName().equals(appName)) {
            this.metadataProxyService.setCache(restApiMetadataDtoListResponse, dtoMetadataDtoListResponse, entityMetadataDtoListResponse, serviceMetadataDtoSingleResponse);
        }
        long s = System.currentTimeMillis();
        this.hostService.addApp(appName);
        this.loadMetaData(appName, restApiMetadataDtoListResponse, dtoMetadataDtoListResponse);
        log.info("应用[{}]GraphQL 初始化结束[{}ms].", (Object)appName, (Object)(System.currentTimeMillis() - s));
    }

    public void removeApp(String appName) {
        if (!StringUtils.isEmpty((CharSequence)appName) && !appName.equals(Apps.getAppName())) {
            log.error("GraphQL卸载表单应用：{}", (Object)appName);
            graphQLMap.remove(appName);
            this.hostService.removeApp(appName);
            docCache.remove(appName);
        }
    }

    public Object refresh(String appName, String source) {
        if (StringUtils.isEmpty((CharSequence)appName)) {
            appName = Apps.getAppName();
        }
        log.info("GraphQL 刷新开始，事件来源：[{}],应用[{}]", (Object)source, (Object)appName);
        this.graphQLObjectTypeService.clearMetadataCache();
        Long s = System.currentTimeMillis();
        this.hostService.addApp(appName);
        this.loadMetaData(appName, null, null);
        log.info("GraphQL 刷新结束[{}ms].", (Object)(System.currentTimeMillis() - s));
        HashMap<String, Object> res = new HashMap<String, Object>();
        res.put("code", 0);
        res.put("message", "success");
        return res;
    }

    public Object getDoc(String appName, String source) {
        ArrayList docDtoList = new ArrayList();
        docCache.forEach((k, v) -> docDtoList.addAll(v));
        HashMap<String, Serializable> res = new HashMap<String, Serializable>();
        res.put("code", Integer.valueOf(0));
        res.put("data", docDtoList);
        return res;
    }

    private synchronized void loadMetaData(String appName, ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse) {
        this.graphQLObjectTypeService.setAppCache(appName);
        GraphQLSchema.Builder builder = new GraphQLSchema.Builder();
        SeeyonSchema schema = new SeeyonSchema();
        ThreadLocalUtil.set((String)"SeeyonSchema", (Object)schema);
        this.addMethod(builder, appName, restApiMetadataDtoListResponse, dtoMetadataDtoListResponse);
        GraphQLSchema graphQLSchema = builder.build();
        DataLoaderDispatcherInstrumentationOptions options = DataLoaderDispatcherInstrumentationOptions.newOptions().includeStatistics(true);
        DataLoaderDispatcherInstrumentation dispatcherInstrumentation = new DataLoaderDispatcherInstrumentation(options);
        GraphQL graphQL = GraphQL.newGraphQL((GraphQLSchema)graphQLSchema).instrumentation((Instrumentation)dispatcherInstrumentation).build();
        graphQLMap.put(appName, graphQL);
        this.schemaCache.add(appName, (SeeyonSchema)ThreadLocalUtil.get((String)"SeeyonSchema"));
        ThreadLocalUtil.remove();
        this.graphQLObjectTypeService.clearAppCache();
        this.graphQLObjectTypeService.clearMetadataCache(appName);
        this.graphQLObjectTypeService.clearTypeNameCache();
        this.graphQLObjectTypeService.clearRestNameCache(appName);
    }

    private void addMethod(GraphQLSchema.Builder baseBuilder, String appName, ListResponse<RestApiMetadataDto> restApiMetadataDtoListResponse, ListResponse<DtoMetadataDto> dtoMetadataDtoListResponse) {
        DataFetcher dataFetcher = dataFetchingEnvironment -> "ok";
        GraphQLObjectType.Builder queryBuilder = GraphQLObjectType.newObject().name("Query").field(GraphQLFieldDefinition.newFieldDefinition().name("health").dataFetcher(dataFetcher).type((GraphQLOutputType)Scalars.GraphQLString));
        GraphQLObjectType.Builder mutationBuilder = GraphQLObjectType.newObject().name("Mutation").field(GraphQLFieldDefinition.newFieldDefinition().name("health").dataFetcher(dataFetcher).type((GraphQLOutputType)Scalars.GraphQLString));
        SeeyonRest rest = new SeeyonRest();
        rest.setAppName(appName);
        rest.setHttpMethod("POST");
        ((SeeyonSchema)ThreadLocalUtil.get((String)"SeeyonSchema")).addRest("health", rest);
        ListResponse restApiMetadata = restApiMetadataDtoListResponse;
        if (null == restApiMetadata) {
            restApiMetadata = ListResponse.from((List)this.metadataProxyService.selectRestApiMetadata(appName));
        }
        if (restApiMetadata.success()) {
            this.graphQLObjectTypeService.refreshDtoCache(appName, restApiMetadata, dtoMetadataDtoListResponse);
            this.graphQLObjectTypeService.clearCacheMapping();
            this.graphQLObjectTypeService.clearDataloaderRegistryCache(appName);
            this.graphQLObjectTypeService.clearDataloaderCache(appName);
            this.graphQLObjectTypeService.clearTypeNameCache();
            this.cleanDocCache(appName);
            List apiList = restApiMetadata.getData().getContent();
            log.info("应用[{}]GraphQL 初始化Rest个数[{}].", (Object)appName, (Object)apiList.size());
            int methodSize = 0;
            if (!CollectionUtils.isEmpty((Collection)apiList)) {
                ArrayList<DocDto> docDtoList = new ArrayList<DocDto>();
                for (RestApiMetadataDto metadataDto : apiList) {
                    List methodList = metadataDto.getMethodList();
                    if (CollectionUtils.isEmpty((Collection)methodList)) continue;
                    for (RestMethodMetadataDto methodDto : methodList) {
                        ++methodSize;
                        DocDto doc = new DocDto();
                        doc.setDescription(methodDto.getCaption() == null ? methodDto.getDescription() : methodDto.getCaption());
                        doc.setCreateDate(DateUtils.formatDatetime((Date)new Date()));
                        docDtoList.add(doc);
                        try {
                            if ("get".equals(methodDto.getHttpMethod().toLowerCase())) {
                                this.queryBuild(doc, baseBuilder, queryBuilder, methodDto, appName);
                            } else {
                                this.queryBuild(doc, baseBuilder, queryBuilder, mutationBuilder, methodDto, appName);
                            }
                            doc.setIsSuccess("true");
                            doc.setMessage("解析正常");
                        }
                        catch (Exception e) {
                            doc.setIsSuccess("false");
                            doc.setMessage(e.getMessage());
                            if ("type can't be null".equals(e.getMessage())) {
                                log.info("方法[{}]初始化GraphQL异常，异常原因:[{}]", (Object)methodDto.getPath(), (Object)e.getMessage());
                                continue;
                            }
                            log.info("方法[{}]初始化GraphQL异常，异常原因:[{}]", (Object)methodDto.getPath(), (Object)e.getMessage());
                        }
                    }
                }
                log.info("应用[{}]GraphQL 初始化Method个数[{}].", (Object)appName, (Object)methodSize);
                docCache.put(appName, docDtoList);
            } else {
                log.info("应用[{}]GraphQL初始化异常,Rest元数据获取为空.", (Object)appName);
            }
        } else {
            log.error("获取元数据RestApi数据失败：[{}]", (Object)restApiMetadata);
        }
        baseBuilder.query(queryBuilder);
        baseBuilder.mutation(mutationBuilder);
    }

    private void queryBuild(DocDto doc, GraphQLSchema.Builder baseBuilder, GraphQLObjectType.Builder queryBuilde, RestMethodMetadataDto methodDto, String appName) throws Exception {
        String methodTypeName = GraphQLProvider.pathToCamel(methodDto.getPath() + "/" + methodDto.getHttpMethod().toLowerCase());
        GraphQLFieldDefinition.Builder builder = GraphQLFieldDefinition.newFieldDefinition();
        builder.name(methodTypeName).description(methodDto.getCaption()).dataFetcher(this.creatDataFetcher(methodDto, appName));
        this.graphQLObjectTypeService.addMethod(doc, baseBuilder, builder, methodDto, appName, methodTypeName);
        queryBuilde.field(builder);
        this.seeyonRest(methodDto, appName, methodTypeName);
    }

    private void queryBuild(DocDto doc, GraphQLSchema.Builder baseBuilder, GraphQLObjectType.Builder queryBuilde, GraphQLObjectType.Builder mutationBuilder, RestMethodMetadataDto methodDto, String appName) throws Exception {
        String methodTypeName = GraphQLProvider.pathToCamel(methodDto.getPath() + "/" + methodDto.getHttpMethod().toLowerCase());
        GraphQLFieldDefinition.Builder builder = GraphQLFieldDefinition.newFieldDefinition();
        builder.name(methodTypeName).description(methodDto.getCaption()).dataFetcher(this.creatDataFetcher(methodDto, appName));
        this.graphQLObjectTypeService.addMethod(doc, baseBuilder, builder, methodDto, appName, methodTypeName);
        queryBuilde.field(builder);
        mutationBuilder.field(builder);
        this.seeyonRest(methodDto, appName, methodTypeName);
    }

    private void seeyonRest(RestMethodMetadataDto methodDto, String appName, String methodTypeName) {
        SeeyonRest rest = new SeeyonRest();
        rest.setPath(methodDto.getPath());
        rest.setHttpMethod(methodDto.getHttpMethod());
        rest.setAppName(appName);
        if (null != ThreadLocalUtil.get((String)"SeeyonSchema")) {
            ((SeeyonSchema)ThreadLocalUtil.get((String)"SeeyonSchema")).addRest(methodTypeName, rest);
        }
    }

    private DataFetcher<?> creatDataFetcher(RestMethodMetadataDto methodDto, String appName) {
        return DynamicDataServletFetcher.build((String)methodDto.getPath(), (String)methodDto.getHttpMethod(), (String)appName, (AppHostService)this.hostService, (SeeyonThreadPool)this.pool);
    }

    private static String pathToCamel(String path) {
        path = path.replaceAll("\\{", "");
        path = path.replaceAll("\\}", "");
        path = GraphQLProvider.toCamelCase(path, false, '-', '/', '_');
        path = path.replaceAll("[^A-Za-z0-9]", "");
        path = path.replaceAll("Id$", "");
        path = path.replaceAll("IdGet$", "Get");
        path = path.replaceAll("SearchPost$", "Search");
        return path;
    }

    public static String toCamelCase(String str, boolean capitalizeFirstLetter, char ... delimiters) {
        if (StringUtils.isEmpty((CharSequence)str)) {
            return str;
        }
        int strLen = str.length();
        int[] newCodePoints = new int[strLen];
        int outOffset = 0;
        Set<Integer> delimiterSet = GraphQLProvider.generateDelimiterSet(delimiters);
        boolean capitalizeNext = false;
        if (capitalizeFirstLetter) {
            capitalizeNext = true;
        }
        int index = 0;
        while (index < strLen) {
            int codePoint = str.codePointAt(index);
            if (delimiterSet.contains(codePoint)) {
                capitalizeNext = true;
                if (outOffset == 0) {
                    capitalizeNext = false;
                }
                index += Character.charCount(codePoint);
                continue;
            }
            if (!(capitalizeNext || outOffset == 0 && capitalizeFirstLetter)) {
                newCodePoints[outOffset++] = codePoint;
                index += Character.charCount(codePoint);
                continue;
            }
            int titleCaseCodePoint = Character.toTitleCase(codePoint);
            newCodePoints[outOffset++] = titleCaseCodePoint;
            index += Character.charCount(titleCaseCodePoint);
            capitalizeNext = false;
        }
        if (outOffset != 0) {
            return new String(newCodePoints, 0, outOffset);
        }
        return str;
    }

    private static Set<Integer> generateDelimiterSet(char[] delimiters) {
        HashSet<Integer> delimiterHashSet = new HashSet<Integer>();
        delimiterHashSet.add(Character.codePointAt(new char[]{' '}, 0));
        if (delimiters != null && delimiters.length != 0) {
            for (int index = 0; index < delimiters.length; ++index) {
                delimiterHashSet.add(Character.codePointAt(delimiters, index));
            }
            return delimiterHashSet;
        }
        return delimiterHashSet;
    }

    public void cleanDocCache(String appName) {
        docCache.remove(appName);
    }
}
