/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.annotation.AnnotationUtil
 *  cn.hutool.core.util.PageUtil
 *  cn.hutool.core.util.ReflectUtil
 *  com.google.common.collect.ArrayListMultimap
 *  com.google.common.collect.Lists
 *  com.google.common.collect.Maps
 *  com.google.common.collect.Multimap
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.annotation.EntityAttribute
 *  com.seeyon.boot.annotation.enums.EntityType
 *  com.seeyon.boot.annotation.enums.RelationType
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.context.RequestContext
 *  com.seeyon.boot.domain.dao.BaseDao
 *  com.seeyon.boot.domain.dao.Wrapper
 *  com.seeyon.boot.domain.entity.BaseEntity
 *  com.seeyon.boot.enums.ActionType
 *  com.seeyon.boot.exception.BootException
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.loader.ModuleAppClassLoader
 *  com.seeyon.boot.loader.ModuleClassLoader
 *  com.seeyon.boot.starter.dynamicsql.appservice.DynamicProxySelectService
 *  com.seeyon.boot.starter.dynamicsql.dto.DynamicConditionDto
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto
 *  com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto
 *  com.seeyon.boot.starter.eventbus.EventBus
 *  com.seeyon.boot.starter.excel.dto.biz.ExcelImportResultDto
 *  com.seeyon.boot.starter.excel.dto.biz.ExcelImportTransDto
 *  com.seeyon.boot.starter.i18n.MessageRepository
 *  com.seeyon.boot.starter.lowcode.annotation.ECacheEvict
 *  com.seeyon.boot.starter.lowcode.annotation.ECachePut
 *  com.seeyon.boot.starter.lowcode.annotation.ECacheable
 *  com.seeyon.boot.starter.lowcode.annotation.PriorityCache
 *  com.seeyon.boot.starter.lowcode.callback.ApprovalCallBack
 *  com.seeyon.boot.starter.lowcode.callback.BillStateCallBack
 *  com.seeyon.boot.starter.lowcode.callback.EntityAttrSnapshotCallBack
 *  com.seeyon.boot.starter.lowcode.callback.MethodCallBack
 *  com.seeyon.boot.starter.lowcode.callback.PermissionCallBack
 *  com.seeyon.boot.starter.lowcode.callback.PreCopyCallBack
 *  com.seeyon.boot.starter.lowcode.callback.PreCreateCallBack
 *  com.seeyon.boot.starter.lowcode.callback.PreUpdateCallBack
 *  com.seeyon.boot.starter.lowcode.callback.SecretCallBack
 *  com.seeyon.boot.starter.lowcode.callback.ValidateCallBack
 *  com.seeyon.boot.starter.lowcode.config.EntityConfig
 *  com.seeyon.boot.starter.lowcode.context.OperateContext
 *  com.seeyon.boot.starter.lowcode.core.BaseCurdService
 *  com.seeyon.boot.starter.lowcode.core.DataTransferService
 *  com.seeyon.boot.starter.lowcode.core.EntityBeanContainer
 *  com.seeyon.boot.starter.lowcode.core.EntityMeta
 *  com.seeyon.boot.starter.lowcode.core.EntityRelationHandler
 *  com.seeyon.boot.starter.lowcode.dto.ApprovalContext
 *  com.seeyon.boot.starter.lowcode.dto.BaseConditionDto
 *  com.seeyon.boot.starter.lowcode.dto.MapConditionDto
 *  com.seeyon.boot.starter.lowcode.enums.RecursiveType
 *  com.seeyon.boot.starter.lowcode.exception.NotSupportedException
 *  com.seeyon.boot.starter.lowcode.exception.thrower.EntityExceptionThrower
 *  com.seeyon.boot.starter.lowcode.helper.DtoFieldHelper
 *  com.seeyon.boot.starter.lowcode.helper.EntityEventHelper
 *  com.seeyon.boot.starter.lowcode.helper.EventContainer
 *  com.seeyon.boot.starter.lowcode.util.CacheUtil
 *  com.seeyon.boot.starter.lowcode.util.DbMap2DtoUtil
 *  com.seeyon.boot.starter.lowcode.util.DtoConvertUtil
 *  com.seeyon.boot.starter.lowcode.util.DynamicConditionUtil
 *  com.seeyon.boot.starter.lowcode.util.EntityMetaUtil
 *  com.seeyon.boot.starter.lowcode.util.QueryConditionUtil
 *  com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil
 *  com.seeyon.boot.starter.lowcode.util.UdcRequestUtil
 *  com.seeyon.boot.starter.module.ModuleBeanFactory
 *  com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao
 *  com.seeyon.boot.starter.mybatis.BaseMybatisDao
 *  com.seeyon.boot.starter.mybatis.EntityClassContext
 *  com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao
 *  com.seeyon.boot.trace.RunnableWrapper
 *  com.seeyon.boot.transport.PageData
 *  com.seeyon.boot.transport.PageInfo
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.transport.Sort
 *  com.seeyon.boot.util.Asserts
 *  com.seeyon.boot.util.JsonUtils
 *  com.seeyon.boot.util.bean.BeanCopier
 *  com.seeyon.boot.util.bean.BeanCopier$CopyStrategy
 *  com.seeyon.boot.util.id.Ids
 *  com.seeyon.udc.common.constant.BillFieldConstant
 *  com.seeyon.udc.common.constant.UdcCommonConstant
 *  com.seeyon.udc.common.datatype.CommonDataTypes
 *  com.seeyon.udc.common.datatype.UdcDataType
 *  com.seeyon.udc.common.dto.BaseDetailDto
 *  com.seeyon.udc.common.dto.BaseEntityActionDto
 *  com.seeyon.udc.common.dto.BaseRootDto
 *  com.seeyon.udc.common.dto.ForceUpdateResultDto
 *  com.seeyon.udc.common.dto.ResultDto
 *  com.seeyon.udc.common.event.ChangeEventData
 *  com.seeyon.udc.common.support.UConsumer
 *  com.seeyon.udc.common.utils.AnnotationUtils
 *  com.seeyon.udc.common.utils.AppNameUtil
 *  com.seeyon.udc.common.utils.EntityUtil
 *  com.seeyon.udc.common.utils.MultiThreadTransaction
 *  com.seeyon.udc.common.utils.MultiThreadTransaction$Result
 *  com.seeyon.udc.common.utils.ResponseUtils
 *  com.seeyon.udc.common.utils.UdcJsonUtils
 *  javax.annotation.Nonnull
 *  org.apache.commons.collections.CollectionUtils
 *  org.apache.commons.collections.MapUtils
 *  org.apache.commons.compress.utils.Sets
 *  org.apache.commons.lang3.EnumUtils
 *  org.apache.commons.lang3.StringUtils
 *  org.apache.commons.lang3.exception.ExceptionUtils
 *  org.jetbrains.annotations.NotNull
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.InitializingBean
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.cache.annotation.CacheConfig
 *  org.springframework.core.ResolvableType
 *  org.springframework.data.util.CastUtils
 *  org.springframework.jdbc.datasource.DataSourceTransactionManager
 *  org.springframework.jdbc.datasource.JdbcTransactionObjectSupport
 *  org.springframework.transaction.PlatformTransactionManager
 *  org.springframework.transaction.TransactionDefinition
 *  org.springframework.transaction.annotation.Propagation
 *  org.springframework.transaction.annotation.Transactional
 *  org.springframework.transaction.support.AbstractPlatformTransactionManager
 *  org.springframework.transaction.support.DefaultTransactionDefinition
 *  org.springframework.transaction.support.DefaultTransactionStatus
 *  org.springframework.transaction.support.TransactionSynchronizationManager
 *  org.springframework.util.Assert
 *  org.springframework.util.StopWatch
 */
package com.seeyon.boot.starter.lowcode.service;

import cn.hutool.core.annotation.AnnotationUtil;
import cn.hutool.core.util.PageUtil;
import cn.hutool.core.util.ReflectUtil;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.annotation.EntityAttribute;
import com.seeyon.boot.annotation.enums.EntityType;
import com.seeyon.boot.annotation.enums.RelationType;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.context.RequestContext;
import com.seeyon.boot.domain.dao.BaseDao;
import com.seeyon.boot.domain.dao.Wrapper;
import com.seeyon.boot.domain.entity.BaseEntity;
import com.seeyon.boot.enums.ActionType;
import com.seeyon.boot.exception.BootException;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.loader.ModuleAppClassLoader;
import com.seeyon.boot.loader.ModuleClassLoader;
import com.seeyon.boot.starter.dynamicsql.appservice.DynamicProxySelectService;
import com.seeyon.boot.starter.dynamicsql.dto.DynamicConditionDto;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyJoinParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.ProxyParamDto;
import com.seeyon.boot.starter.dynamicsql.dto.QueryConditionDto;
import com.seeyon.boot.starter.eventbus.EventBus;
import com.seeyon.boot.starter.excel.dto.biz.ExcelImportResultDto;
import com.seeyon.boot.starter.excel.dto.biz.ExcelImportTransDto;
import com.seeyon.boot.starter.i18n.MessageRepository;
import com.seeyon.boot.starter.lowcode.annotation.ECacheEvict;
import com.seeyon.boot.starter.lowcode.annotation.ECachePut;
import com.seeyon.boot.starter.lowcode.annotation.ECacheable;
import com.seeyon.boot.starter.lowcode.annotation.PriorityCache;
import com.seeyon.boot.starter.lowcode.callback.ApprovalCallBack;
import com.seeyon.boot.starter.lowcode.callback.BillStateCallBack;
import com.seeyon.boot.starter.lowcode.callback.EntityAttrSnapshotCallBack;
import com.seeyon.boot.starter.lowcode.callback.MethodCallBack;
import com.seeyon.boot.starter.lowcode.callback.PermissionCallBack;
import com.seeyon.boot.starter.lowcode.callback.PreCopyCallBack;
import com.seeyon.boot.starter.lowcode.callback.PreCreateCallBack;
import com.seeyon.boot.starter.lowcode.callback.PreUpdateCallBack;
import com.seeyon.boot.starter.lowcode.callback.SecretCallBack;
import com.seeyon.boot.starter.lowcode.callback.ValidateCallBack;
import com.seeyon.boot.starter.lowcode.config.EntityConfig;
import com.seeyon.boot.starter.lowcode.context.OperateContext;
import com.seeyon.boot.starter.lowcode.core.BaseCurdService;
import com.seeyon.boot.starter.lowcode.core.DataTransferService;
import com.seeyon.boot.starter.lowcode.core.EntityBeanContainer;
import com.seeyon.boot.starter.lowcode.core.EntityMeta;
import com.seeyon.boot.starter.lowcode.core.EntityRelationHandler;
import com.seeyon.boot.starter.lowcode.dto.ApprovalContext;
import com.seeyon.boot.starter.lowcode.dto.BaseConditionDto;
import com.seeyon.boot.starter.lowcode.dto.MapConditionDto;
import com.seeyon.boot.starter.lowcode.enums.RecursiveType;
import com.seeyon.boot.starter.lowcode.exception.NotSupportedException;
import com.seeyon.boot.starter.lowcode.exception.thrower.EntityExceptionThrower;
import com.seeyon.boot.starter.lowcode.helper.DtoFieldHelper;
import com.seeyon.boot.starter.lowcode.helper.EntityEventHelper;
import com.seeyon.boot.starter.lowcode.helper.EventContainer;
import com.seeyon.boot.starter.lowcode.util.CacheUtil;
import com.seeyon.boot.starter.lowcode.util.DbMap2DtoUtil;
import com.seeyon.boot.starter.lowcode.util.DtoConvertUtil;
import com.seeyon.boot.starter.lowcode.util.DynamicConditionUtil;
import com.seeyon.boot.starter.lowcode.util.EntityMetaUtil;
import com.seeyon.boot.starter.lowcode.util.QueryConditionUtil;
import com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil;
import com.seeyon.boot.starter.lowcode.util.UdcRequestUtil;
import com.seeyon.boot.starter.module.ModuleBeanFactory;
import com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao;
import com.seeyon.boot.starter.mybatis.BaseMybatisDao;
import com.seeyon.boot.starter.mybatis.EntityClassContext;
import com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao;
import com.seeyon.boot.trace.RunnableWrapper;
import com.seeyon.boot.transport.PageData;
import com.seeyon.boot.transport.PageInfo;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.transport.Sort;
import com.seeyon.boot.util.Asserts;
import com.seeyon.boot.util.JsonUtils;
import com.seeyon.boot.util.bean.BeanCopier;
import com.seeyon.boot.util.id.Ids;
import com.seeyon.udc.common.constant.BillFieldConstant;
import com.seeyon.udc.common.constant.UdcCommonConstant;
import com.seeyon.udc.common.datatype.CommonDataTypes;
import com.seeyon.udc.common.datatype.UdcDataType;
import com.seeyon.udc.common.dto.BaseDetailDto;
import com.seeyon.udc.common.dto.BaseEntityActionDto;
import com.seeyon.udc.common.dto.BaseRootDto;
import com.seeyon.udc.common.dto.ForceUpdateResultDto;
import com.seeyon.udc.common.dto.ResultDto;
import com.seeyon.udc.common.event.ChangeEventData;
import com.seeyon.udc.common.support.UConsumer;
import com.seeyon.udc.common.utils.AnnotationUtils;
import com.seeyon.udc.common.utils.AppNameUtil;
import com.seeyon.udc.common.utils.EntityUtil;
import com.seeyon.udc.common.utils.MultiThreadTransaction;
import com.seeyon.udc.common.utils.ResponseUtils;
import com.seeyon.udc.common.utils.UdcJsonUtils;
import java.io.Serializable;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiConsumer;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.sql.DataSource;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.MapUtils;
import org.apache.commons.compress.utils.Sets;
import org.apache.commons.lang3.EnumUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.jetbrains.annotations.NotNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheConfig;
import org.springframework.core.ResolvableType;
import org.springframework.data.util.CastUtils;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.JdbcTransactionObjectSupport;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.AbstractPlatformTransactionManager;
import org.springframework.transaction.support.DefaultTransactionDefinition;
import org.springframework.transaction.support.DefaultTransactionStatus;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.util.Assert;
import org.springframework.util.StopWatch;

@CacheConfig(cacheNames={"entity"}, cacheManager="entityRedisCacheManager")
public abstract class BaseEntityCurdService<D extends BaseEntityActionDto>
implements InitializingBean,
BaseCurdService<D>,
PreCreateCallBack<D>,
PreUpdateCallBack<D>,
MethodCallBack<D>,
ValidateCallBack<D>,
DataTransferService<D>,
PreCopyCallBack<D> {
    private static final Logger log = LoggerFactory.getLogger(BaseEntityCurdService.class);
    private static final String HANDLE_EXISTING_TRANSACTION = "handleExistingTransaction";
    private Class<D> dtoClass;
    private Class<?> entityClass;
    private boolean isMasterEntity;
    private EntityMeta entityMeta;
    @Autowired
    private EntityEventHelper entityEventHelper;
    @Autowired
    private EntityBeanContainer entityBeanContainer;
    @Autowired
    private PermissionCallBack permissionCallBack;
    @Autowired
    private ApprovalCallBack approvalCallBack;
    @Autowired
    private BillStateCallBack billStateCallBack;
    @Autowired
    private ExecutorService executorService;
    @Autowired
    private EntityConfig entityConfig;
    @Autowired
    private MultiThreadTransaction threadTransaction;
    @Autowired
    private EventBus eventBus;
    @Autowired
    private PlatformTransactionManager transactionManager;
    @Autowired
    private DynamicProxySelectService dynamicProxySelectService;
    @Autowired
    private ModuleBeanFactory moduleBeanFactory;
    @Autowired
    private CommonDataTypes commonDataTypes;
    @Autowired
    private MessageRepository messageRepository;
    @Autowired
    private SecretCallBack secretCallBack;
    @Autowired
    private EntityAttrSnapshotCallBack entityAttrSnapshotCallBack;
    private BiConsumer<EntityMeta, List<D>> beforeUpdateConsumer = (meta, dtoList) -> Optional.ofNullable(this.entityBeanContainer.findService(meta.getDtoClass())).ifPresent(service -> service.beforeUpdate(dtoList));

    private static <D extends BaseEntityActionDto> void handlerCaseId(@NotNull D dto) {
        Long caseId;
        Object caseIdObj = ReflectFieldUtil.getFieldValue(dto, (String)"caseId");
        if (Objects.nonNull(caseIdObj) && (caseId = (Long)CastUtils.cast((Object)caseIdObj)) != 0L && !UdcRequestUtil.isActionFromBpm((BaseRootDto)((BaseRootDto)dto))) {
            log.warn("来自于非bpm调用，新建数据携带了caseId");
        }
    }

    public void afterPropertiesSet() throws Exception {
        this.asyncInit();
    }

    public void asyncInit() {
        ResolvableType resolvableType = this.getClass().getName().contains("$$") ? ResolvableType.forClass(this.getClass().getSuperclass()).getSuperType() : ResolvableType.forClass(this.getClass()).getSuperType();
        ResolvableType[] types = resolvableType.getGenerics();
        this.dtoClass = types[0].resolve();
        String dtoClassName = this.dtoClass.getName();
        String appName = AppNameUtil.getAppNameByDtoFullName((String)dtoClassName);
        Assert.notNull(this.dtoClass, (String)"泛型类标识错误");
        Map relationMap = EntityRelationHandler.parse((ClassLoader)this.dtoClass.getClassLoader(), (String)appName);
        DtoInfo dtoInfo = (DtoInfo)AnnotationUtil.getAnnotation(this.dtoClass, DtoInfo.class);
        this.entityMeta = (EntityMeta)relationMap.get(dtoInfo.entity());
        Assert.notNull((Object)this.entityMeta, (String)(this.dtoClass.getSimpleName() + "找不到关联实体:" + dtoInfo.entity()));
        this.entityClass = this.entityMeta.getEntityClass();
        this.isMasterEntity = EntityType.MASTER_ENTITY == this.entityMeta.getEntityType();
    }

    public Class<D> getDtoClass() {
        return this.dtoClass;
    }

    public <DAO extends BaseDao> DAO getMapper() {
        return (DAO)this.entityBeanContainer.findDao(this.entityClass);
    }

    private void resetNormal(List<D> dList) {
        Consumer<BaseEntityActionDto> consumer = DtoFieldHelper::resetChildNormal;
        dList.stream().forEach(newDto -> {
            newDto.setActionType(ActionType.NORMAL);
            DtoConvertUtil.forEach((EntityMeta)this.entityMeta, (BaseEntityActionDto)newDto, (Consumer)consumer);
        });
    }

    public int operateRootBatch(List<D> list) {
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        BaseEntityCurdService baseEntityCurdService = this.getBaseEntityCurdService();
        Map dtoGroupMap = DtoConvertUtil.groupByAction(list);
        AtomicInteger count = new AtomicInteger(0);
        Optional.ofNullable(dtoGroupMap.get(ActionType.DELETE)).ifPresent(deleteList -> {
            if (CollectionUtils.isNotEmpty((Collection)deleteList)) {
                List<Long> ids = deleteList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                int i = baseEntityCurdService.deleteByIds(ids);
                count.set(count.get() + i);
            }
        });
        Optional.ofNullable(dtoGroupMap.get(ActionType.UPDATE)).ifPresent(updateList -> {
            if (CollectionUtils.isNotEmpty((Collection)updateList)) {
                int i = baseEntityCurdService.updateBatch((List)updateList);
                count.set(count.get() + i);
            }
        });
        Optional.ofNullable(dtoGroupMap.get(ActionType.INSERT)).ifPresent(insertList -> {
            if (CollectionUtils.isNotEmpty((Collection)insertList)) {
                int i = baseEntityCurdService.createBatch((List)insertList);
                count.set(count.get() + i);
            }
        });
        return count.get();
    }

    @Transactional(propagation=Propagation.REQUIRED)
    public int create(@Nonnull D dto) {
        this.printTransactionInfo();
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        BaseEntityCurdService.handlerCaseId(dto);
        BiConsumer<BaseEntityActionDto, BaseEntityActionDto> biConsumer = DtoFieldHelper::resetInsert;
        DtoConvertUtil.resetInsertHandle((EntityMeta)this.entityMeta, dto, biConsumer);
        ArrayList newDtoList = Lists.newArrayList((Object[])new BaseEntityActionDto[]{dto});
        BiConsumer<EntityMeta, List> setSubEntityConsumer = DtoFieldHelper::setSubEntityOrderNo;
        DtoConvertUtil.forEach((EntityMeta)this.entityMeta, (List)newDtoList, setSubEntityConsumer);
        StopWatch stopWatch = new StopWatch();
        if (this.isMasterEntity && Objects.nonNull(this.permissionCallBack)) {
            stopWatch.start("表单权限:赋初值");
            this.permissionCallBack.buildInitialValue(this.entityMeta, null, dto);
            stopWatch.stop();
        }
        stopWatch.start("默认值/计算");
        this.preCreateBatch(newDtoList);
        stopWatch.stop();
        if (this.isMasterEntity && Objects.nonNull(this.permissionCallBack)) {
            stopWatch.start("表单权限:必填");
            this.permissionCallBack.requiredValidate(this.entityMeta, null, dto);
            stopWatch.stop();
        }
        this.beforeCreate(newDtoList);
        stopWatch.start("新建前事件");
        EventContainer container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.INSERT).eventData((Collection)Lists.newArrayList((Object[])new BaseEntityActionDto[]{dto})).build() : null;
        this.entityEventHelper.beforeEvent(container);
        stopWatch.stop();
        stopWatch.start("新建前校验");
        this.afterBeforeEventCheck(newDtoList);
        stopWatch.stop();
        EntityExceptionThrower.throwing((List)newDtoList);
        OperateContext context = OperateContext.builder().actionType(ActionType.INSERT).entityMeta(this.entityMeta).newData((List)CastUtils.cast((Object)newDtoList)).build();
        context.enter();
        if (this.isMasterEntity && null != this.secretCallBack) {
            this.secretCallBack.checkSecret((Collection)newDtoList);
        }
        stopWatch.start("新建子孙实体");
        this.recursiveCheck(this.entityMeta, newDtoList, null);
        int i = this.recursiveCreate(this.entityMeta, newDtoList);
        stopWatch.stop();
        stopWatch.start("入库主实体");
        this.middleCreate(newDtoList);
        BaseEntity entity = (BaseEntity)BeanCopier.copy(dto, this.entityClass, (String[])new String[0]);
        Object mapper = this.getMapper();
        int j = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.create((Object)entity));
        this.afterCreate(newDtoList);
        stopWatch.stop();
        stopWatch.start("新增后事件");
        this.entityEventHelper.afterEvent(container);
        stopWatch.stop();
        stopWatch.start("新增后事务完成事件");
        dto.setId(entity.getId());
        context.leave();
        this.resetNormal(newDtoList);
        this.entityEventHelper.transactionSuccessEvent(container);
        stopWatch.stop();
        log.info("新建数据:{}-{}\n{}", new Object[]{this.entityMeta.getCaption(), dto.getId(), stopWatch.prettyPrint()});
        return j;
    }

    public int createBatch(List<D> dtos) {
        if (CollectionUtils.isEmpty(dtos)) {
            return 0;
        }
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        BiConsumer<BaseEntityActionDto, BaseEntityActionDto> biConsumer = DtoFieldHelper::resetInsert;
        dtos.stream().forEach(d -> DtoConvertUtil.resetInsertHandle((EntityMeta)this.entityMeta, (BaseEntityActionDto)d, (BiConsumer)biConsumer));
        StopWatch stopWatch = new StopWatch();
        stopWatch.start("默认值/计算");
        this.preCreateBatch(dtos);
        this.beforeCreate(dtos);
        stopWatch.stop();
        stopWatch.start("新建前事件");
        EventContainer container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.INSERT).eventData((Collection)Lists.newArrayList(dtos)).build() : null;
        this.entityEventHelper.beforeEvent(container);
        stopWatch.stop();
        stopWatch.start("新建前校验");
        this.afterBeforeEventCheck(dtos);
        stopWatch.stop();
        EntityExceptionThrower.throwing(dtos);
        OperateContext context = OperateContext.builder().actionType(ActionType.INSERT).entityMeta(this.entityMeta).newData((List)CastUtils.cast(dtos)).build();
        context.enter();
        if (this.isMasterEntity && null != this.secretCallBack) {
            this.secretCallBack.checkSecret(dtos);
        }
        stopWatch.start("新建子孙实体");
        this.recursiveCheck(this.entityMeta, dtos, null);
        int i = this.recursiveCreate(this.entityMeta, dtos);
        stopWatch.stop();
        stopWatch.start("入库主实体");
        this.middleCreate(dtos);
        List entityList = BeanCopier.copyList(dtos, this.entityClass);
        Object mapper = this.getMapper();
        int j = (Integer)EntityClassContext.withEntityClass(mapper, this.getEntityClass(), () -> mapper.createBatch(entityList));
        this.afterCreate(dtos);
        stopWatch.stop();
        stopWatch.start("新增后事件");
        this.entityEventHelper.afterEvent(container);
        stopWatch.stop();
        context.leave();
        stopWatch.start("新增后事务完成事件");
        this.resetNormal(dtos);
        this.entityEventHelper.transactionSuccessEvent(container);
        stopWatch.stop();
        log.info("批量新建数据:{}\n{}", (Object)this.entityMeta.getCaption(), (Object)stopWatch.prettyPrint());
        return j;
    }

    private int recursiveCreate(EntityMeta entityMeta, List<D> newDtoList) {
        AtomicInteger count = new AtomicInteger(0);
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            if (CollectionUtils.isNotEmpty(newDtoList)) {
                newDtoList.stream().forEach(newDto -> entityMeta.getChildren().stream().forEach(meta -> {
                    Object dtoList = ReflectFieldUtil.getFieldValue((Object)newDto, (String)meta.getDtoListName());
                    if (Objects.nonNull(dtoList)) {
                        ArrayList dtoColl = Lists.newArrayList();
                        if (dtoList instanceof Collection) {
                            dtoColl.addAll((Collection)dtoList);
                        } else {
                            dtoColl.add((BaseEntityActionDto)dtoList);
                        }
                        if (CollectionUtils.isNotEmpty((Collection)meta.getChildren())) {
                            int i = this.recursiveCreate((EntityMeta)meta, dtoColl);
                            count.set(count.get() + i);
                        }
                        Optional.ofNullable(this.entityBeanContainer.findDao(meta.getEntityClass())).ifPresent(mybatisDao -> {
                            List insetEntityList = BeanCopier.copyList((Collection)dtoColl, (Class)meta.getEntityClass());
                            BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(meta.getDtoClass());
                            Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.beforeCreate(dtoColl));
                            int k = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)meta.getEntityClass(), () -> mybatisDao.createBatch(insetEntityList));
                            Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.afterCreate(dtoColl));
                            count.set(count.get() + k);
                        });
                    }
                }));
            }
        } else if (EntityType.MASTER_ENTITY != entityMeta.getEntityType()) {
            Optional.ofNullable(this.entityBeanContainer.findDao(entityMeta.getEntityClass())).ifPresent(mybatisDao -> {
                List insetEntityList = BeanCopier.copyList((Collection)newDtoList, (Class)entityMeta.getEntityClass());
                BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(entityMeta.getDtoClass());
                Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.beforeCreate(newDtoList));
                int k = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)entityMeta.getEntityClass(), () -> mybatisDao.createBatch(insetEntityList));
                count.set(count.get() + k);
                Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.afterCreate(newDtoList));
            });
        }
        return count.get();
    }

    public Long copyAndInsert(Long id) {
        BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        D dto = baseEntityCurdService.selectCascadeById(id);
        Optional.ofNullable(dto).orElseThrow(() -> new BusinessException("BOOT_4002"));
        dto.setId(null);
        dto.setCreateTime(null);
        dto.setUpdateTime(null);
        BiConsumer<BaseEntityActionDto, BaseEntityActionDto> consumer = DtoFieldHelper::resetId;
        DtoConvertUtil.resetInsertHandle((EntityMeta)this.entityMeta, dto, consumer);
        baseEntityCurdService.create(dto);
        return dto.getId();
    }

    public D runtimeCopy(Long id) {
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        D dto = this.selectCascadeById(id);
        Optional.ofNullable(dto).orElseThrow(() -> new BusinessException("BOOT_4002"));
        this.preCopyBatch(Collections.singletonList(dto));
        BiConsumer<BaseEntityActionDto, BaseEntityActionDto> consumer = DtoFieldHelper::resetId;
        DtoConvertUtil.resetInsertHandle((EntityMeta)this.entityMeta, dto, consumer);
        this.resetNormal(Collections.singletonList(dto));
        return dto;
    }

    @ECacheEvict
    @Transactional(propagation=Propagation.REQUIRED)
    public D updateWithResult(@Nonnull D newDto) {
        try {
            HashSet<String> ignoreSet = new HashSet<String>();
            ignoreSet.add(this.entityClass.getName());
            Apps.ignorePermission(ignoreSet);
            this.update(newDto);
        }
        finally {
            Apps.ignorePermissionFinish();
        }
        return newDto;
    }

    @ECachePut
    public D createWithResult(@Nonnull D newDto) {
        this.create(newDto);
        newDto.setActionType(ActionType.NORMAL);
        Consumer<BaseEntityActionDto> consumer = DtoFieldHelper::resetChildNormal;
        DtoConvertUtil.forEach((EntityMeta)this.entityMeta, newDto, consumer);
        return newDto;
    }

    @ECacheEvict
    public int update(@Nonnull D newDto) {
        return this.updateBase(newDto, true, false);
    }

    @ECacheEvict
    public int updateNoEvents(@Nonnull D newDto) {
        return this.updateBase(newDto, false, false);
    }

    public int updateWithFields(Map<String, Object> entityMap) {
        BaseEntityActionDto newDto;
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        Long id = MapUtils.getLong(entityMap, (Object)"id");
        if (id == null) {
            log.error("主实体ID不能为空, entityMap: {}", entityMap);
            throw BusinessException.message((String)"主实体id不能为空!");
        }
        try {
            newDto = (BaseEntityActionDto)ReflectFieldUtil.getInstance(this.dtoClass);
        }
        catch (Exception e) {
            log.error("实体dto实例化失败!", (Throwable)e);
            throw BusinessException.message((String)"实体dto实例化失败!");
        }
        newDto.setValidate(true);
        newDto.setDraft(Boolean.valueOf(false));
        List children = this.entityMeta.getChildren();
        HashMap childEntityDtoOrDtoListNameMap = new HashMap();
        if (CollectionUtils.isNotEmpty((Collection)children)) {
            childEntityDtoOrDtoListNameMap.putAll(children.stream().collect(Collectors.toMap(EntityMeta::getDtoListName, Function.identity())));
        }
        ArrayList<String> updatedFields = new ArrayList<String>();
        ReflectUtil.setFieldValue((Object)newDto, (String)"actionType", (Object)ActionType.UPDATE);
        for (Map.Entry<String, Object> entry : entityMap.entrySet()) {
            String fieldName = entry.getKey();
            Object fieldValue = entry.getValue();
            Field field = ReflectFieldUtil.getField(this.dtoClass, (String)fieldName);
            if (field == null) {
                log.error("字段 field: {} 不存在", (Object)fieldName);
                continue;
            }
            if (childEntityDtoOrDtoListNameMap.containsKey(fieldName)) {
                EntityMeta childEntityMeta = (EntityMeta)childEntityDtoOrDtoListNameMap.get(fieldName);
                if (RelationType.One2ManyAggregation == childEntityMeta.getRelationType()) {
                    List childList = (List)fieldValue;
                    if (!CollectionUtils.isNotEmpty((Collection)childList)) continue;
                    ArrayList childDtoList = Lists.newArrayList();
                    for (Map entityData : childList) {
                        Object one2ManyChildDto = this.getChildDtoFromMap(entityData, childEntityMeta);
                        childDtoList.add(one2ManyChildDto);
                    }
                    ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)childDtoList);
                    continue;
                }
                if (RelationType.One2OneAggregation != childEntityMeta.getRelationType()) continue;
                Object one2ManyChildDto = this.getChildDtoFromMap((Map)fieldValue, childEntityMeta);
                ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)one2ManyChildDto);
                continue;
            }
            updatedFields.add(fieldName);
            ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)fieldValue);
        }
        ReflectUtil.setFieldValue((Object)newDto, (String)"__updatedFields", updatedFields);
        return this.updateBase(newDto, true, true);
    }

    private Object getChildDtoFromMap(Map<String, Object> entityData, EntityMeta currentEntityMeta) {
        this.checkChildEntityData(entityData);
        Class dtoClass = currentEntityMeta.getDtoClass();
        Object newDto = ReflectFieldUtil.getInstance((Class)dtoClass);
        ReflectUtil.setFieldValue((Object)newDto, (String)"actionType", (Object)ActionType.UPDATE);
        HashMap childEntityDtoOrDtoListNameMap = new HashMap();
        List children = currentEntityMeta.getChildren();
        if (CollectionUtils.isNotEmpty((Collection)children)) {
            childEntityDtoOrDtoListNameMap.putAll(children.stream().collect(Collectors.toMap(EntityMeta::getDtoListName, Function.identity())));
        }
        ArrayList<String> updatedFields = new ArrayList<String>();
        for (Map.Entry<String, Object> entry : entityData.entrySet()) {
            String fieldName = entry.getKey();
            Object fieldValue = entry.getValue();
            Field field = ReflectFieldUtil.getField((Class)dtoClass, (String)fieldName);
            if (field == null) {
                log.error("字段 field: {} 不存在", (Object)fieldName);
                continue;
            }
            if (childEntityDtoOrDtoListNameMap.containsKey(fieldName)) {
                EntityMeta childEntityMeta = (EntityMeta)childEntityDtoOrDtoListNameMap.get(fieldName);
                if (RelationType.One2ManyAggregation == childEntityMeta.getRelationType()) {
                    List childList = (List)fieldValue;
                    if (!CollectionUtils.isNotEmpty((Collection)childList)) continue;
                    ArrayList childDtoList = Lists.newArrayList();
                    for (Map childEntityData : childList) {
                        Object one2ManyChildDto = this.getChildDtoFromMap(childEntityData, childEntityMeta);
                        childDtoList.add(one2ManyChildDto);
                    }
                    ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)childDtoList);
                    continue;
                }
                if (RelationType.One2OneAggregation != childEntityMeta.getRelationType()) continue;
                Object one2ManyChildDto = this.getChildDtoFromMap((Map)fieldValue, childEntityMeta);
                ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)one2ManyChildDto);
                continue;
            }
            updatedFields.add(fieldName);
            ReflectUtil.setFieldValue((Object)newDto, (String)fieldName, (Object)fieldValue);
        }
        ReflectUtil.setFieldValue((Object)newDto, (String)"__updatedFields", updatedFields);
        return newDto;
    }

    private void checkChildEntityData(Map<String, Object> childDataMap) {
        Long id = MapUtils.getLong(childDataMap, (Object)"id");
        Long parentId = MapUtils.getLong(childDataMap, (Object)"parentId");
        if (id == null) {
            throw BusinessException.message((String)"子表id不能为空!");
        }
    }

    private int updateBase(@Nonnull D newDto, boolean sendEvent, boolean needIgnoreVersion) {
        this.printTransactionInfo();
        if (this.entityConfig.isEnableLog()) {
            log.info("newDto:{}", (Object)JsonUtils.toJson(newDto));
        }
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        Asserts.notNull((Object)newDto.getId(), (String)"id");
        newDto.setActionType(ActionType.UPDATE);
        StopWatch stopWatch = new StopWatch();
        stopWatch.start("计算/默认规则");
        ArrayList frontDtoList = Lists.newArrayList((Object[])new BaseEntityActionDto[]{newDto});
        DtoConvertUtil.forEach((EntityMeta)this.entityMeta, (List)frontDtoList, this.beforeUpdateConsumer);
        Map newMap = DtoConvertUtil.defaultUpdateListToMap((EntityMeta)this.entityMeta, (List)frontDtoList);
        stopWatch.stop();
        stopWatch.start("修改数据查询");
        D oldDto = this.selectCascadeById(newDto.getId());
        stopWatch.stop();
        stopWatch.start("数据合并");
        if (StringUtils.isNotBlank((CharSequence)this.entityMeta.getStereotype()) && !"standard".equals(this.entityMeta.getStereotype())) {
            HashMap<String, Enum> extendMap = newDto.getExtendMap();
            if (Objects.isNull(extendMap)) {
                extendMap = new HashMap<String, Enum>();
            }
            Enum oldStatusType = (Enum)ReflectFieldUtil.getFieldValue(oldDto, (String)"statusType");
            extendMap.put("oldStatusType", oldStatusType);
            newDto.setExtendMap(extendMap);
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("数据库 oldDto:{}", (Object)JsonUtils.toJson(oldDto));
        }
        if (Objects.isNull(oldDto)) {
            throw new BusinessException("BOOT_4002");
        }
        Map oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, (List)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}));
        OperateContext context = OperateContext.builder().actionType(ActionType.UPDATE).entityMeta(this.entityMeta).newData((List)CastUtils.cast((Object)Lists.newArrayList((Object[])new BaseEntityActionDto[]{newDto}))).oldData((List)CastUtils.cast((Object)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}))).build();
        context.enter();
        context.deepCopyNewData();
        List newDtoList = DtoConvertUtil.mergeMapData((EntityMeta)this.entityMeta, (Map)oldMap, (Map)newMap);
        newDto = (BaseEntityActionDto)newDtoList.iterator().next();
        stopWatch.stop();
        stopWatch.start("表单权限");
        if (this.isMasterEntity) {
            if (Objects.nonNull(this.billStateCallBack)) {
                this.billStateCallBack.checkBillState(oldDto, newDto);
            }
            if (Objects.nonNull(this.permissionCallBack)) {
                this.permissionCallBack.buildInitialValue(this.entityMeta, oldDto, newDto);
            }
            this.preUpdateBatch(newDtoList);
            if (Objects.nonNull(this.permissionCallBack)) {
                this.permissionCallBack.requiredValidate(this.entityMeta, oldDto, newDto);
            }
        }
        EventContainer container = null;
        if (sendEvent) {
            ChangeEventData changeData = new ChangeEventData();
            changeData.setCurrent(newDto);
            changeData.setPrevious(oldDto);
            container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.UPDATE).changeData((Collection)Lists.newArrayList((Object[])new ChangeEventData[]{changeData})).build() : null;
            stopWatch.stop();
            stopWatch.start("新增前事件");
            this.entityEventHelper.beforeEvent(container);
        }
        stopWatch.stop();
        stopWatch.start("入库前校验");
        this.afterBeforeEventCheck(newDtoList);
        stopWatch.stop();
        EntityExceptionThrower.throwing(Collections.singletonList(newDto));
        if (this.isMasterEntity) {
            if (null != this.secretCallBack) {
                this.secretCallBack.checkSecret((Collection)newDtoList);
            }
            stopWatch.start("更新实体字段快照");
            this.entityAttrSnapshotCallBack.updateSnapshot(newDtoList, newMap, oldMap, this.entityMeta);
            stopWatch.stop();
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("更新前merge后、预处理、表单操作权限、处理后数据:{}", (Object)JsonUtils.toJson((Object)newDtoList));
        }
        stopWatch.start("入库子表");
        int i = this.deleteData(this.entityMeta, newMap);
        this.recursiveCheck(this.entityMeta, newDtoList, oldMap);
        int j = this.recursiveUpdate(this.entityMeta, newDtoList, oldMap);
        stopWatch.stop();
        stopWatch.start("入库主表");
        BaseEntity entity = (BaseEntity)BeanCopier.copy(newDto, this.entityClass, (String[])new String[0]);
        if (this.entityConfig.isEnableLog()) {
            log.info("主实体{},更新前数据：{}", entity.getClass(), (Object)entity);
        }
        Object mapper = this.getMapper();
        int k = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> needIgnoreVersion ? mapper.versionNoUpdateBatchIgnoreVersion((List)Lists.newArrayList((Object[])new BaseEntity[]{entity})) : mapper.update((Object)entity));
        if (sendEvent) {
            stopWatch.stop();
            stopWatch.start("更新后事件");
            this.entityEventHelper.afterEvent(container);
        }
        this.afterUpdate(frontDtoList, oldMap);
        context.leave();
        if (sendEvent) {
            stopWatch.stop();
            stopWatch.start("更新事务提交后事件");
            this.resetNormal(Lists.newArrayList((Object[])new BaseEntityActionDto[]{newDto}));
            this.entityEventHelper.transactionSuccessEvent(container);
        }
        newMap = null;
        oldMap = null;
        stopWatch.stop();
        log.info("更新数据:{}-{}\n{}", new Object[]{this.entityMeta.getCaption(), newDto.getId(), stopWatch.prettyPrint()});
        return k;
    }

    protected BaseEntityCurdService<D> getBaseEntityCurdService() {
        BaseEntityCurdService service;
        ClassLoader classLoader = this.getClass().getClassLoader();
        if (ModuleClassLoader.class.isAssignableFrom(classLoader.getClass())) {
            String beanPrefix = "l" + Integer.toHexString(classLoader.hashCode()) + ".";
            String formBeanFullName = beanPrefix + this.getClass().getName();
            service = (BaseEntityCurdService)Apps.getApplicationContext().getBean(formBeanFullName, BaseEntityCurdService.class);
            if (Objects.isNull(service)) {
                service = (BaseEntityCurdService)Apps.getApplicationContext().getBean(this.getClass());
            }
        } else if (ModuleAppClassLoader.class.isAssignableFrom(classLoader.getClass())) {
            String formBeanFullName = this.getClass().getName();
            service = (BaseEntityCurdService)this.moduleBeanFactory.getBean(this.getClass());
        } else {
            service = (BaseEntityCurdService)Apps.getApplicationContext().getBean(this.getClass());
        }
        return service;
    }

    private int deleteData(EntityMeta entityMeta, Map<Long, D> newMap) {
        return this.deleteData(entityMeta, newMap, false);
    }

    private int deleteData(EntityMeta entityMeta, Map<Long, D> newMap, boolean adminUpdate) {
        AtomicInteger count = new AtomicInteger(0);
        Map<Class, List<BaseEntityActionDto>> deleteMap = newMap.values().stream().filter(d -> ActionType.DELETE == d.getActionType()).collect(Collectors.groupingBy(d -> d.getClass()));
        if (MapUtils.isNotEmpty(deleteMap)) {
            Consumer<EntityMeta> deleteConsumer = meta -> {
                List deleteList = (List)deleteMap.get(meta.getDtoClass());
                if (CollectionUtils.isNotEmpty((Collection)deleteList)) {
                    Optional.ofNullable(this.entityBeanContainer.findDao(meta.getEntityClass())).ifPresent(mybatisDao -> {
                        List allIds = deleteList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                        List partIds = Lists.partition(allIds, (int)1000);
                        for (List ids : partIds) {
                            BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(meta.getDtoClass());
                            if (!adminUpdate) {
                                Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.beforeDelete(deleteList));
                            }
                            int j = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)meta.getEntityClass(), () -> mybatisDao.deleteByIds(ids));
                            count.set(count.get() + j);
                            Optional.ofNullable(baseEntityCurdService).ifPresent(service -> {
                                if (!adminUpdate) {
                                    service.afterDelete(deleteList);
                                }
                                CacheUtil.evict(service.getClass(), (Collection)ids);
                            });
                        }
                    });
                }
            };
            EntityMetaUtil.forEachMeta((EntityMeta)entityMeta, deleteConsumer);
        }
        return count.get();
    }

    private int recursiveUpdate(EntityMeta entityMeta, List<D> newDtoList, Map<Long, D> oldMap) {
        return this.recursiveUpdate(entityMeta, newDtoList, oldMap, false);
    }

    private int recursiveUpdate(EntityMeta entityMeta, List<D> newDtoList, Map<Long, D> oldMap, boolean adminUpdate) {
        AtomicInteger count = new AtomicInteger(0);
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            if (CollectionUtils.isNotEmpty(newDtoList)) {
                newDtoList.forEach(newDto -> entityMeta.getChildren().forEach(meta -> {
                    Object dtoList = ReflectFieldUtil.getFieldValue((Object)newDto, (String)meta.getDtoListName());
                    if (Objects.nonNull(dtoList)) {
                        ArrayList dtoColl = Lists.newArrayList();
                        if (dtoList instanceof Collection) {
                            dtoColl.addAll((Collection)dtoList);
                        } else {
                            dtoColl.add((BaseEntityActionDto)dtoList);
                        }
                        if (CollectionUtils.isNotEmpty((Collection)meta.getChildren())) {
                            int i = this.recursiveUpdate((EntityMeta)meta, dtoColl, oldMap, adminUpdate);
                            count.set(count.get() + i);
                        }
                        this.handleSelfUpdate(count, (EntityMeta)meta, dtoColl, oldMap, adminUpdate);
                    }
                }));
            }
        } else if (EntityType.MASTER_ENTITY != entityMeta.getEntityType()) {
            this.handleSelfUpdate(count, entityMeta, newDtoList, oldMap, adminUpdate);
        }
        return count.get();
    }

    private void recursiveCheck(EntityMeta entityMeta, List<D> newDtoList, Map<Long, D> oldMap) {
        if (CollectionUtils.isEmpty((Collection)entityMeta.getChildren())) {
            return;
        }
        StringBuilder msg = new StringBuilder();
        this.recursiveCheck(entityMeta, newDtoList, oldMap, msg);
        if (msg.length() > 0) {
            throw new BusinessException("UDC_COMMON_0003", new String[]{msg.toString()});
        }
    }

    private void recursiveCheck(EntityMeta entityMeta, List<D> newDtoList, Map<Long, D> oldMap, StringBuilder msg) {
        if (CollectionUtils.isEmpty((Collection)entityMeta.getChildren())) {
            return;
        }
        newDtoList.forEach(newDto -> entityMeta.getChildren().forEach(meta -> {
            Object dtoList = ReflectFieldUtil.getFieldValue((Object)newDto, (String)meta.getDtoListName());
            if (Objects.nonNull(dtoList)) {
                ArrayList dtoColl = Lists.newArrayList();
                if (dtoList instanceof Collection) {
                    dtoColl.addAll((Collection)dtoList);
                } else {
                    dtoColl.add((BaseEntityActionDto)dtoList);
                }
                String errorMsg = this.checkSystemAttribute(newDto, dtoColl, newDtoList, oldMap);
                msg.append(errorMsg);
                if (CollectionUtils.isNotEmpty((Collection)meta.getChildren())) {
                    this.recursiveCheck((EntityMeta)meta, dtoColl, oldMap, msg);
                }
            }
        }));
    }

    private String checkSystemAttribute(D parentDto, List<D> childDtoList, List<D> newDtoList, Map<Long, D> oldMap) {
        ActionType parentactionType = parentDto.getActionType();
        Long parentId = parentDto.getId();
        StringBuilder errorMsg = new StringBuilder();
        for (BaseEntityActionDto child2 : childDtoList) {
            Object parentIdObj = ReflectFieldUtil.getFieldValue((Object)child2, (String)"parentId");
            if (Objects.equals(UdcCommonConstant.NULL_ID, parentIdObj) || Objects.isNull(parentIdObj)) {
                ReflectFieldUtil.setFieldValue((Object)child2, (String)"parentId", (Object)parentId);
                continue;
            }
            if (Objects.equals(parentId, parentIdObj)) continue;
            String message = this.messageRepository.getMessage("error.code.ENTITY_0031", (Object[])new String[]{child2.getClass().getName(), String.valueOf(parentIdObj), String.valueOf(parentId)});
            log.error(message);
            errorMsg.append(message).append(";");
        }
        if (ActionType.UPDATE == parentactionType && Objects.nonNull(oldMap)) {
            if (!oldMap.containsKey(parentId)) {
                String message = this.messageRepository.getMessage("error.code.ENTITY_0032", (Object[])new String[]{parentDto.getClass().getName(), String.valueOf(parentId)});
                log.error(message);
                errorMsg.append(message).append(";");
            }
            childDtoList.stream().filter(child -> ActionType.UPDATE.equals((Object)child.getActionType())).forEach(child -> {
                if (!oldMap.containsKey(child.getId())) {
                    String message = this.messageRepository.getMessage("error.code.ENTITY_0032", (Object[])new String[]{child.getClass().getName(), String.valueOf(child.getId())});
                    log.error(message);
                    errorMsg.append(message).append(";");
                }
            });
        }
        return errorMsg.toString();
    }

    private void handleSelfUpdate(AtomicInteger count, EntityMeta meta, List<D> dtoColl, Map<Long, D> oldMap, boolean adminUpdate) {
        Optional.ofNullable(this.entityBeanContainer.findDao(meta.getEntityClass())).ifPresent(mybatisDao -> {
            Map<ActionType, List<BaseEntityActionDto>> actionTypeMap = dtoColl.stream().filter(a -> Objects.nonNull(a.getActionType())).collect(Collectors.groupingBy(BaseEntityActionDto::getActionType));
            actionTypeMap.forEach((key, value) -> {
                if (ActionType.INSERT == key) {
                    List insetEntityList = adminUpdate ? BeanCopier.copyList((Collection)value, (Class)meta.getEntityClass(), (BeanCopier.CopyStrategy)BeanCopier.CopyStrategy.IGNORE_NULL, (String[])new String[0]) : BeanCopier.copyList((Collection)value, (Class)meta.getEntityClass());
                    BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(meta.getDtoClass());
                    if (!adminUpdate) {
                        Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.beforeCreate(value));
                    }
                    int i = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)meta.getEntityClass(), () -> mybatisDao.createBatch(insetEntityList));
                    for (int j = 0; j < insetEntityList.size(); ++j) {
                        ((BaseEntityActionDto)value.get(j)).setId(((BaseEntity)insetEntityList.get(j)).getId());
                    }
                    count.set(count.get() + i);
                    if (!adminUpdate) {
                        Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.afterCreate(value));
                    }
                } else if (ActionType.UPDATE == key) {
                    List updateEntityList = BeanCopier.copyList((Collection)value, (Class)meta.getEntityClass());
                    int i = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)meta.getEntityClass(), () -> mybatisDao.updateBatch(updateEntityList));
                    count.set(count.get() + i);
                    BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(meta.getDtoClass());
                    List ids = value.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                    Optional.ofNullable(baseEntityCurdService).ifPresent(service -> {
                        if (!adminUpdate) {
                            service.afterUpdate(value, oldMap);
                        }
                        CacheUtil.evict(service.getClass(), (Collection)ids);
                    });
                }
            });
        });
    }

    public int updateRootEntity(D newRootDto) {
        D oldRootDto = this.selectCascadeById(newRootDto.getId());
        if (Objects.nonNull(oldRootDto)) {
            return this.updateRootEntity(oldRootDto, newRootDto);
        }
        return 0;
    }

    public int updateRootEntity(@Nonnull D oldRootDto, @Nonnull D newRootDto) {
        if (Objects.nonNull(newRootDto)) {
            Consumer<BaseEntityActionDto> consumer = DtoFieldHelper::resetChildNormal;
            newRootDto = DtoConvertUtil.forEach((EntityMeta)this.entityMeta, newRootDto, consumer);
            newRootDto.setActionType(ActionType.UPDATE);
            if (newRootDto instanceof BaseRootDto) {
                ((BaseRootDto)newRootDto).getLinkSourceIds().clear();
            }
        }
        ChangeEventData changeData = new ChangeEventData();
        changeData.setCurrent(newRootDto);
        changeData.setPrevious(oldRootDto);
        EventContainer container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.UPDATE).changeData((Collection)Lists.newArrayList((Object[])new ChangeEventData[]{changeData})).build() : null;
        this.entityEventHelper.beforeEvent(container);
        BaseEntity entity = (BaseEntity)BeanCopier.copy(newRootDto, this.entityClass, (String[])new String[0]);
        int i = 0;
        Object mapper = this.getMapper();
        i = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.updateColumnsIgnoreVersion((Object)entity, this.getUpdateRootFiled(entity)));
        CacheUtil.evict(this.getClass(), (Collection)Lists.newArrayList((Object[])new Long[]{newRootDto.getId()}));
        this.entityEventHelper.afterEvent(container);
        this.entityEventHelper.transactionSuccessEvent(container);
        return i;
    }

    public int updateStatusType(@Nonnull D rootDto) {
        BaseEntity entity = (BaseEntity)BeanCopier.copy(rootDto, this.entityClass, (String[])new String[0]);
        Object mapper = this.getMapper();
        int i = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.updateColumnsIgnoreVersion((Object)entity, (Set)Sets.newHashSet((Object[])new String[]{"statusType"})));
        return i;
    }

    @ECacheEvict
    public List<D> updateBatchWithResult(@Nonnull List<D> newDtoList) {
        this.updateBatch(newDtoList);
        return newDtoList;
    }

    @ECacheEvict
    public int updateBatch(@Nonnull List<D> newDtoList) {
        EventContainer container;
        if (CollectionUtils.isEmpty(newDtoList)) {
            return 0;
        }
        StopWatch stopWatch = new StopWatch();
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        List<Long> dtoIds = newDtoList.stream().map(d -> {
            d.setActionType(ActionType.UPDATE);
            return d.getId();
        }).filter(Objects::nonNull).collect(Collectors.toList());
        Asserts.notEmpty(dtoIds, (String)"更新数据id列表");
        Map newMap = DtoConvertUtil.defaultUpdateListToMap((EntityMeta)this.entityMeta, newDtoList);
        DtoConvertUtil.forEach((EntityMeta)this.entityMeta, newDtoList, this.beforeUpdateConsumer);
        List<D> oldDtoList = this.selectCascadeByIds(dtoIds);
        if (CollectionUtils.isEmpty(oldDtoList)) {
            throw new BusinessException("BOOT_4002");
        }
        Map oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, oldDtoList);
        OperateContext context = OperateContext.builder().actionType(ActionType.UPDATE).entityMeta(this.entityMeta).newData((List)CastUtils.cast(newDtoList)).oldData((List)CastUtils.cast(oldDtoList)).build();
        context.enter();
        context.deepCopyNewData();
        newDtoList = DtoConvertUtil.mergeMapData((EntityMeta)this.entityMeta, (Map)oldMap, (Map)newMap);
        if (this.isMasterEntity) {
            if (Objects.nonNull(this.billStateCallBack)) {
                for (BaseEntityActionDto newDto : newDtoList) {
                    Optional.ofNullable(oldMap.get(newDto.getId())).ifPresent(oldDto -> this.billStateCallBack.checkBillState(oldDto, newDto));
                }
            }
            if (Objects.nonNull(this.permissionCallBack)) {
                for (BaseEntityActionDto newDto : newDtoList) {
                    Optional.ofNullable(oldMap.get(newDto.getId())).ifPresent(oldDto -> this.permissionCallBack.buildInitialValue(this.entityMeta, oldDto, newDto));
                }
            }
            this.preUpdateBatch(newDtoList);
            if (Objects.nonNull(this.permissionCallBack)) {
                for (BaseEntityActionDto newDto : newDtoList) {
                    Optional.ofNullable(oldMap.get(newDto.getId())).ifPresent(oldDto -> this.permissionCallBack.requiredValidate(this.entityMeta, oldDto, newDto));
                }
            }
        }
        Map masterEntityMap = null;
        if (this.isMasterEntity && CollectionUtils.isNotEmpty(oldDtoList)) {
            masterEntityMap = oldDtoList.stream().collect(Collectors.toMap(o -> o.getId(), Function.identity()));
        }
        ArrayList changeDataList = null;
        if (this.isMasterEntity && MapUtils.isNotEmpty(masterEntityMap)) {
            changeDataList = Lists.newArrayList();
            for (BaseEntityActionDto d2 : newDtoList) {
                if (!masterEntityMap.containsKey(d2.getId())) continue;
                ChangeEventData changeData = new ChangeEventData();
                changeData.setCurrent(d2);
                changeData.setPrevious((BaseEntityActionDto)masterEntityMap.get(d2.getId()));
                changeDataList.add(changeData);
            }
            EventContainer container2 = EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.UPDATE).changeData((Collection)changeDataList).build();
            this.entityEventHelper.beforeEvent(container2);
        }
        this.afterBeforeEventCheck(newDtoList);
        EntityExceptionThrower.throwing((List)newDtoList);
        if (this.isMasterEntity) {
            if (null != this.secretCallBack) {
                this.secretCallBack.checkSecret((Collection)newDtoList);
            }
            stopWatch.start("【批量】更新实体字段快照");
            this.entityAttrSnapshotCallBack.updateSnapshot(newDtoList, newMap, oldMap, this.entityMeta);
            stopWatch.stop();
        }
        int i = this.deleteData(this.entityMeta, newMap);
        this.recursiveCheck(this.entityMeta, newDtoList, oldMap);
        int j = this.recursiveUpdate(this.entityMeta, newDtoList, oldMap);
        List entityList = BeanCopier.copyList((Collection)newDtoList, this.entityClass);
        Object mapper = this.getMapper();
        int k = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.updateBatch(entityList));
        if (this.isMasterEntity && MapUtils.isNotEmpty(masterEntityMap)) {
            container = EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.UPDATE).changeData((Collection)changeDataList).build();
            this.entityEventHelper.afterEvent(container);
        }
        this.afterUpdate(newDtoList, oldMap);
        context.leave();
        if (this.isMasterEntity && MapUtils.isNotEmpty(masterEntityMap)) {
            if (CollectionUtils.isNotEmpty((Collection)newDtoList)) {
                this.resetNormal(newDtoList);
            }
            container = EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.UPDATE).changeData((Collection)Lists.newArrayList((Iterable)changeDataList)).build();
            this.entityEventHelper.transactionSuccessEvent(container);
        }
        newMap = null;
        oldMap = null;
        return k;
    }

    @ECacheable
    public D selectCascadeById(Long id) {
        if (this.entityConfig.isParallelHandle()) {
            return this.doParallelSelectCascadeById(id);
        }
        return this.doSelectCascadeById(id);
    }

    public D doSelectCascadeById(Long id) {
        if (Objects.isNull(id)) {
            return null;
        }
        BaseEntityActionDto dto = this.selectById(id);
        if (Objects.isNull(dto)) {
            if (this.entityConfig.isEnableLog()) {
                log.info("db dto is null:{}", (Object)id);
            }
            return null;
        }
        if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren())) {
            this.entityMeta.getChildren().stream().forEach(subMeta -> this.setSingeSubDtoList(id, (D)dto, (EntityMeta)subMeta, null));
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("db dto:{}", (Object)JsonUtils.toJson((Object)dto));
        }
        return (D)dto;
    }

    public D doParallelSelectCascadeById(Long id) {
        List validSubEntityMetaList;
        if (Objects.isNull(id)) {
            return null;
        }
        DataSource dataSource = ((DataSourceTransactionManager)this.transactionManager).getDataSource();
        DefaultTransactionDefinition transactionDefinition = new DefaultTransactionDefinition();
        DefaultTransactionStatus mainTxStatus = (DefaultTransactionStatus)this.transactionManager.getTransaction((TransactionDefinition)transactionDefinition);
        JdbcTransactionObjectSupport txObject = (JdbcTransactionObjectSupport)mainTxStatus.getTransaction();
        BaseEntityActionDto dto = this.selectById(id);
        if (Objects.isNull(dto)) {
            if (this.entityConfig.isEnableLog()) {
                log.info("db dto is null:{}", (Object)id);
            }
            return null;
        }
        if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren()) && CollectionUtils.isNotEmpty(validSubEntityMetaList = this.entityMeta.getChildren().stream().filter(e -> null != this.entityBeanContainer.findService(e.getDtoClass())).collect(Collectors.toList()))) {
            ArrayList<CompletableFuture<Void>> futureList = new ArrayList<CompletableFuture<Void>>(validSubEntityMetaList.size());
            for (EntityMeta subMeta : validSubEntityMetaList) {
                BaseEntityCurdService subService = this.entityBeanContainer.findService(subMeta.getDtoClass());
                CompletableFuture<Void> subEntityFuture = CompletableFuture.runAsync((Runnable)RunnableWrapper.of(() -> {
                    try {
                        Method handleExistingTransactionMethod = AbstractPlatformTransactionManager.class.getDeclaredMethod(HANDLE_EXISTING_TRANSACTION, TransactionDefinition.class, Object.class, Boolean.TYPE);
                        handleExistingTransactionMethod.setAccessible(true);
                        handleExistingTransactionMethod.invoke((Object)this.transactionManager, new DefaultTransactionDefinition(), txObject, false);
                        List subDtoList = subService.selectListByCondition("parentId", id, (Sort)(subMeta.isSortField() ? DEFAULT_SORT : null));
                        if (CollectionUtils.isNotEmpty((Collection)subDtoList)) {
                            try {
                                if (RelationType.One2OneAggregation == subMeta.getRelationType()) {
                                    ReflectUtil.setFieldValue((Object)dto, (String)subMeta.getDtoListName(), subDtoList.get(0));
                                } else if (RelationType.One2ManyAggregation == subMeta.getRelationType()) {
                                    ReflectUtil.setFieldValue((Object)dto, (String)subMeta.getDtoListName(), (Object)subDtoList);
                                }
                            }
                            catch (Exception e) {
                                log.error("并行子查询异常: ", (Throwable)e);
                            }
                            this.handleSubRelation(subDtoList, subMeta, null);
                        }
                        if (this.entityConfig.isEnableLog()) {
                            log.info("父dto:{},子subDtoList:{}", (Object)JsonUtils.toJson((Object)dto), (Object)JsonUtils.toJson((Object)subDtoList));
                        }
                    }
                    catch (IllegalAccessException | NoSuchMethodException | InvocationTargetException e) {
                        String errMsg = "实体级联查询调用事务传播方法失败";
                        log.error(errMsg, (Throwable)e);
                        BootException.throwIt((String)errMsg);
                    }
                }), this.executorService);
                futureList.add(subEntityFuture);
            }
            CompletableFuture.allOf(futureList.toArray(new CompletableFuture[validSubEntityMetaList.size()])).join();
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("db dto:{}", (Object)JsonUtils.toJson((Object)dto));
        }
        return (D)dto;
    }

    private void setSingeSubDtoList(Long parentId, D dto, EntityMeta subMeta, Supplier<Map<String, MapConditionDto>> supplier) {
        Optional.ofNullable(this.entityBeanContainer.findService(subMeta.getDtoClass())).ifPresent(subService -> {
            List subDtoList = Collections.emptyList();
            if (supplier != null && supplier.get() != null) {
                if (((Map)supplier.get()).containsKey(subMeta.getFullName())) {
                    HashMap columnMap = Optional.ofNullable(((Map)supplier.get()).get(subMeta.getFullName())).map(MapConditionDto::getColumnMap).orElseGet(() -> Maps.newHashMap());
                    columnMap.put("parentId", parentId);
                    Sort sort = Optional.ofNullable(((Map)supplier.get()).get(subMeta.getFullName())).map(MapConditionDto::getSort).orElseGet(() -> subMeta.isSortField() ? DEFAULT_SORT : null);
                    subDtoList = subService.selectListByConditions(columnMap, sort);
                }
            } else {
                subDtoList = subService.selectListByCondition("parentId", parentId, (Sort)(subMeta.isSortField() ? DEFAULT_SORT : null));
            }
            if (CollectionUtils.isNotEmpty((Collection)subDtoList)) {
                try {
                    if (RelationType.One2OneAggregation == subMeta.getRelationType()) {
                        ReflectUtil.setFieldValue((Object)dto, (String)subMeta.getDtoListName(), subDtoList.get(0));
                    } else if (RelationType.One2ManyAggregation == subMeta.getRelationType()) {
                        ReflectUtil.setFieldValue((Object)dto, (String)subMeta.getDtoListName(), (Object)subDtoList);
                    }
                }
                catch (Exception e) {
                    log.warn(e.getMessage());
                }
                this.handleSubRelation(subDtoList, subMeta, supplier);
            }
            if (this.entityConfig.isEnableLog()) {
                log.info("父dto:{},子subDtoList:{}", (Object)JsonUtils.toJson((Object)dto), (Object)JsonUtils.toJson((Object)subDtoList));
            }
        });
    }

    private void setMultiSubDtoList(Collection<Long> parentIds, List<D> dtoList, EntityMeta subMeta, Supplier<Map<String, MapConditionDto>> supplier) {
        if (CollectionUtils.isEmpty(parentIds)) {
            return;
        }
        Optional.ofNullable(this.entityBeanContainer.findService(subMeta.getDtoClass())).ifPresent(subService -> {
            ArrayList subDtoList = Lists.newArrayList();
            List partIds = Lists.partition((List)Lists.newArrayList((Iterable)parentIds), (int)1000);
            for (List parts : partIds) {
                List partDtoList = Collections.emptyList();
                if (supplier != null && supplier.get() != null) {
                    if (((Map)supplier.get()).containsKey(subMeta.getFullName())) {
                        HashMap columnMap = Optional.ofNullable(((Map)supplier.get()).get(subMeta.getFullName())).map(MapConditionDto::getColumnMap).orElseGet(() -> Maps.newHashMap());
                        columnMap.put("IN_parentId", parts);
                        Sort sort = Optional.ofNullable(((Map)supplier.get()).get(subMeta.getFullName())).map(MapConditionDto::getSort).orElseGet(() -> subMeta.isSortField() ? DEFAULT_SORT : null);
                        partDtoList = subService.selectListByConditions(columnMap, sort);
                    }
                } else {
                    partDtoList = subService.selectListByCondition("IN_parentId", parts, (Sort)(subMeta.isSortField() ? DEFAULT_SORT : null));
                }
                subDtoList.addAll(partDtoList);
            }
            if (CollectionUtils.isNotEmpty((Collection)subDtoList)) {
                ArrayListMultimap sonMultimap = ArrayListMultimap.create();
                subDtoList.stream().forEach(arg_0 -> BaseEntityCurdService.lambda$null$59((Multimap)sonMultimap, arg_0));
                dtoList.stream().forEach(arg_0 -> BaseEntityCurdService.lambda$null$61(subMeta, (Multimap)sonMultimap, arg_0));
                this.handleSubRelation(subDtoList, subMeta, supplier);
            }
            if (this.entityConfig.isEnableLog()) {
                log.info("父dtoList:{},子subDtoList:{}", (Object)JsonUtils.toJson((Object)dtoList), (Object)JsonUtils.toJson((Object)subDtoList));
            }
        });
    }

    private void handleSubRelation(List<BaseEntityActionDto> subDtoList, EntityMeta subMeta, Supplier supplier) {
        if (CollectionUtils.isNotEmpty(subDtoList) && CollectionUtils.isNotEmpty((Collection)subMeta.getChildren())) {
            List subIds = subDtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
            subMeta.getChildren().stream().forEach(arg_0 -> this.lambda$handleSubRelation$64(subDtoList, (Supplier)supplier, subIds, arg_0));
        }
    }

    void recursiveSelect(Collection<Long> ids, List<D> dtoList) {
        if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren())) {
            this.entityMeta.getChildren().stream().forEach(subMeta -> this.setMultiSubDtoList(ids, dtoList, (EntityMeta)subMeta, null));
        }
    }

    void recursiveSelectWithCondition(Collection<Long> ids, List<D> dtoList, Map<String, MapConditionDto> conditionMap) {
        if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren())) {
            this.entityMeta.getChildren().stream().forEach(subMeta -> this.setMultiSubDtoList(ids, dtoList, (EntityMeta)subMeta, () -> conditionMap));
        }
    }

    @PriorityCache(cacheName="entity", cacheManager="entityRedisCacheManager", isAggregateRoot=true)
    public List<D> selectCascadeByIds(Collection<Long> ids) {
        if (CollectionUtils.isEmpty(ids)) {
            return Collections.emptyList();
        }
        List dtoList = this.selectByIds(ids);
        if (CollectionUtils.isEmpty((Collection)dtoList)) {
            return Collections.emptyList();
        }
        this.recursiveSelect(ids, dtoList);
        return dtoList;
    }

    public List<D> selectCascadeListByWrapper(Wrapper wrapper) {
        Object mapper = this.getMapper();
        List entityList = (List)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.selectListByWrapper(wrapper));
        if (CollectionUtils.isEmpty((Collection)entityList)) {
            return Collections.emptyList();
        }
        List dtoList = BeanCopier.copyList((Collection)entityList, this.dtoClass);
        List<Long> ids = dtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
        this.recursiveSelect(ids, dtoList);
        return dtoList;
    }

    public List<D> selectCascadeListByWrapper(Wrapper wrapper, List<MapConditionDto> conditionList) {
        Object mapper = this.getMapper();
        List entityList = (List)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.selectListByWrapper(wrapper));
        if (CollectionUtils.isEmpty((Collection)entityList)) {
            return Collections.emptyList();
        }
        List dtoList = BeanCopier.copyList((Collection)entityList, this.dtoClass);
        List<Long> ids = dtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
        Map<String, MapConditionDto> conditionMap = conditionList.stream().collect(Collectors.toMap(BaseConditionDto::getEntityFullName, Function.identity()));
        this.recursiveSelectWithCondition(ids, dtoList, conditionMap);
        return dtoList;
    }

    public List<D> selectCascadeListByConditions(List<MapConditionDto> conditionList) {
        if (CollectionUtils.isEmpty(conditionList)) {
            return Collections.emptyList();
        }
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        Map<String, MapConditionDto> conditionMap = conditionList.stream().collect(Collectors.toMap(BaseConditionDto::getEntityFullName, Function.identity()));
        MapConditionDto conditionDto = (MapConditionDto)conditionMap.get(this.entityMeta.getFullName());
        if (Objects.isNull(conditionDto)) {
            return Collections.emptyList();
        }
        List dtoList = this.selectListByConditions(conditionDto.getColumnMap(), conditionDto.getSort());
        List<Long> ids = dtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
        this.recursiveSelectWithCondition(ids, dtoList, conditionMap);
        return dtoList;
    }

    @ECacheEvict
    public int deleteById(@Nonnull Long id) {
        Map oldMap;
        BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        D oldDto = baseEntityCurdService.selectCascadeById(id);
        if (Objects.isNull(oldDto)) {
            return 0;
        }
        OperateContext context = OperateContext.builder().actionType(ActionType.DELETE).entityMeta(this.entityMeta).oldData((List)CastUtils.cast((Object)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}))).newData((List)CastUtils.cast((Object)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}))).build();
        context.enter();
        this.beforeDelete(Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}));
        EventContainer container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.DELETE).eventData((Collection)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto})).build() : null;
        this.entityEventHelper.beforeEvent(container);
        AtomicInteger count = new AtomicInteger(0);
        if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren()) && MapUtils.isNotEmpty((Map)(oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, (List)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}))))) {
            this.entityMeta.getChildren().stream().forEach(subMeta -> {
                int i = this.recursiveDelete((EntityMeta)subMeta, oldMap);
                count.set(count.get() + i);
            });
            if (log.isInfoEnabled()) {
                log.info("删除实体:{}下子实体数据共：{}条", (Object)this.entityMeta.getFullName(), (Object)count.get());
            }
        }
        Object mapper = this.getMapper();
        int i = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.deleteById(id));
        this.afterDelete(Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}));
        context.leave();
        if (this.isMasterEntity) {
            this.entityAttrSnapshotCallBack.deleteByDataMasterIds((List)Lists.newArrayList((Object[])new Long[]{id}));
        }
        this.entityEventHelper.afterEvent(container);
        this.entityEventHelper.transactionSuccessEvent(container);
        log.info("userId:[{}]-ip:[{}]删除实体:[{}],id:[{}]", new Object[]{Apps.getRequestContext().getUserId(), Apps.getRequestContext().getClientIp(), this.entityMeta.getFullName(), id});
        return i;
    }

    @ECacheEvict
    public int deleteByIds(Collection<Long> ids) {
        if (CollectionUtils.isEmpty(ids)) {
            return 0;
        }
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
        AtomicInteger count = new AtomicInteger(0);
        List partIds = Lists.partition((List)((List)ids), (int)1000);
        for (List parts : partIds) {
            Map oldMap;
            List<D> oldDtoList = baseEntityCurdService.selectCascadeByIds(parts);
            if (CollectionUtils.isEmpty(oldDtoList)) {
                return count.get();
            }
            OperateContext context = OperateContext.builder().actionType(ActionType.DELETE).entityMeta(this.entityMeta).oldData((List)CastUtils.cast(oldDtoList)).newData((List)CastUtils.cast(oldDtoList)).build();
            context.enter();
            this.beforeDelete(oldDtoList);
            EventContainer container = this.isMasterEntity ? EventContainer.builder().dtoClass(this.dtoClass).actionType(ActionType.DELETE).eventData((Collection)Lists.newArrayList(oldDtoList)).build() : null;
            this.entityEventHelper.beforeEvent(container);
            if (CollectionUtils.isNotEmpty((Collection)this.entityMeta.getChildren()) && MapUtils.isNotEmpty((Map)(oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, oldDtoList)))) {
                this.entityMeta.getChildren().stream().forEach(subMeta -> {
                    int i = this.recursiveDelete((EntityMeta)subMeta, oldMap);
                    count.set(count.get() + i);
                });
                if (log.isInfoEnabled()) {
                    log.info("删除实体:{}下子实体数据共：{}条", (Object)this.entityMeta.getFullName(), (Object)count.get());
                }
            }
            Object mapper = this.getMapper();
            int i = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.deleteByIds((List)Lists.newArrayList((Iterable)parts)));
            count.set(count.get() + i);
            if (this.isMasterEntity) {
                this.entityAttrSnapshotCallBack.deleteByDataMasterIds((List)Lists.newArrayList(ids));
            }
            this.afterDelete(oldDtoList);
            context.leave();
            this.entityEventHelper.afterEvent(container);
            this.entityEventHelper.transactionSuccessEvent(container);
        }
        log.info("userId:[{}]-ip:[{}]删除实体:[{}],ids:[{}]", new Object[]{Apps.getRequestContext().getUserId(), Apps.getRequestContext().getClientIp(), this.entityMeta.getFullName(), ids});
        return count.get();
    }

    private int recursiveDelete(EntityMeta subMeta, Map<Long, D> dbMap) {
        AtomicInteger count = new AtomicInteger(0);
        Optional.ofNullable(this.entityBeanContainer.findDao(subMeta.getEntityClass())).ifPresent(mybatisDao -> {
            List dtoList = dbMap.values().stream().filter(d -> d.getClass().equals(subMeta.getDtoClass())).collect(Collectors.toList());
            if (CollectionUtils.isNotEmpty(dtoList)) {
                List subIds = dtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                if (CollectionUtils.isNotEmpty((Collection)subMeta.getChildren())) {
                    subMeta.getChildren().stream().forEach(meta -> {
                        int k = this.recursiveDelete((EntityMeta)meta, dbMap);
                        count.set(count.get() + k);
                    });
                }
                BaseEntityCurdService baseEntityCurdService = this.entityBeanContainer.findService(subMeta.getDtoClass());
                Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.beforeDelete(dtoList));
                List parentIds = dtoList.stream().map(dto -> ReflectFieldUtil.getFieldValue((Object)dto, (String)"parentId")).distinct().collect(Collectors.toList());
                int i = 0;
                if (CollectionUtils.isNotEmpty(parentIds)) {
                    List partIds = Lists.partition((List)Lists.newArrayList(parentIds), (int)1000);
                    for (List parts : partIds) {
                        i = (Integer)EntityClassContext.withEntityClass((BaseDao)mybatisDao, (Class)subMeta.getEntityClass(), () -> mybatisDao.deleteByCondition("IN_parentId", (Object)parts));
                    }
                }
                Optional.ofNullable(baseEntityCurdService).ifPresent(service -> service.afterDelete(dtoList));
                if (log.isInfoEnabled()) {
                    log.info("删除实体:{}下子实体数据共：{}条", (Object)subMeta.getFullName(), (Object)i);
                }
                count.set(count.get() + i);
            }
        });
        return count.get();
    }

    public int deleteByComplexConditions(Map<String, Object> map) {
        Object mapper = this.getMapper();
        return (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> {
            if (mapper instanceof BaseMybatisDao) {
                List list = ((BaseMybatisDao)mapper).selectListByComplexConditions(new LinkedHashMap(map), null);
                Collection ids = list.stream().map(BaseEntity::getId).collect(Collectors.toList());
                return this.deleteByIds(ids);
            }
            if (mapper instanceof AllInOneBaseDao) {
                List list = ((AbstractAllInOneBaseDao)mapper).selectListByComplexConditions((LinkedHashMap)map, null);
                Collection ids = list.stream().map(BaseEntity::getId).collect(Collectors.toList());
                return this.deleteByIds(ids);
            }
            throw new NotSupportedException();
        });
    }

    public Map<Long, D> listToMap(List<D> dtoList) {
        return DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, dtoList);
    }

    private List<D> validateCreate(List<D> validateCreateList) {
        if (CollectionUtils.isNotEmpty(validateCreateList)) {
            BiConsumer<BaseEntityActionDto, BaseEntityActionDto> consumer = DtoFieldHelper::resetInsert;
            validateCreateList.stream().forEach(d -> DtoConvertUtil.resetInsertHandle((EntityMeta)this.entityMeta, (BaseEntityActionDto)d, (BiConsumer)consumer));
            this.preCreateBatch(validateCreateList);
        }
        return validateCreateList;
    }

    private List<D> validateUpdate(List<D> validateUpdateList) {
        if (CollectionUtils.isNotEmpty(validateUpdateList)) {
            List<Long> ids = validateUpdateList.stream().map(BaseEntityActionDto::getId).filter(Objects::nonNull).collect(Collectors.toList());
            if (CollectionUtils.isEmpty(ids)) {
                return validateUpdateList;
            }
            List<D> oldDtoList = this.selectCascadeByIds(ids);
            if (CollectionUtils.isEmpty(oldDtoList)) {
                return validateUpdateList;
            }
            Map newMap = DtoConvertUtil.defaultUpdateListToMap((EntityMeta)this.entityMeta, validateUpdateList);
            Map oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, oldDtoList);
            validateUpdateList = DtoConvertUtil.mergeMapData((EntityMeta)this.entityMeta, (Map)oldMap, (Map)newMap);
            if (Objects.nonNull(this.permissionCallBack)) {
                validateUpdateList.forEach(newDto -> Optional.ofNullable(oldMap.get(newDto.getId())).ifPresent(oldDto -> this.permissionCallBack.buildInitialValue(this.entityMeta, oldDto, newDto)));
            }
            this.preUpdateBatch(validateUpdateList);
            if (Objects.nonNull(this.permissionCallBack)) {
                validateUpdateList.forEach(newDto -> Optional.ofNullable(oldMap.get(newDto.getId())).ifPresent(oldDto -> this.permissionCallBack.requiredValidate(this.entityMeta, oldDto, newDto)));
            }
        }
        return validateUpdateList;
    }

    public D validate(D dto) {
        if (Objects.isNull(dto)) {
            return null;
        }
        if (ActionType.INSERT == dto.getActionType()) {
            List<D> list = this.validateCreate(Lists.newArrayList((Object[])new BaseEntityActionDto[]{dto}));
            ApprovalContext context = new ApprovalContext();
            context.putProcessData(dto);
            this.approvalCallBack.beforeApprovalCreateValidate(context);
            if (CollectionUtils.isNotEmpty(list)) {
                return (D)((BaseEntityActionDto)list.get(0));
            }
        } else if (ActionType.UPDATE == dto.getActionType()) {
            List<D> list = this.validateUpdate(Lists.newArrayList((Object[])new BaseEntityActionDto[]{dto}));
            ApprovalContext context = new ApprovalContext();
            context.putProcessData(dto);
            this.approvalCallBack.beforeApprovalUpdateValidate(context);
            if (CollectionUtils.isNotEmpty(list)) {
                return (D)((BaseEntityActionDto)list.get(0));
            }
        }
        return dto;
    }

    public D getCascadeDefaultValue() {
        Long userId = RequestContext.get().getUserId();
        String cascadeDefaultValueKey = "CascadeDefaultValue:" + userId;
        return this.getCascadeDefaultValue(cascadeDefaultValueKey);
    }

    @ECacheable
    public D getCascadeDefaultValue(String cascadeDefaultValueKey) {
        BaseEntityActionDto defaultValueDto = (BaseEntityActionDto)this.getDefaultValue();
        this.recursiveDefaultValue(this.entityMeta, defaultValueDto);
        return (D)defaultValueDto;
    }

    private void recursiveDefaultValue(EntityMeta entityMeta, D currentDto) {
        if (Objects.isNull(currentDto)) {
            return;
        }
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            entityMeta.getChildren().stream().forEach(meta -> Optional.ofNullable(this.entityBeanContainer.findService(meta.getDtoClass())).ifPresent(service -> {
                BaseEntityActionDto defaultValueDto = (BaseEntityActionDto)service.getDefaultValue();
                if (Objects.nonNull(defaultValueDto)) {
                    if (RelationType.One2OneAggregation == meta.getRelationType()) {
                        ReflectUtil.setFieldValue((Object)currentDto, (String)meta.getDtoListName(), (Object)defaultValueDto);
                    } else if (RelationType.One2ManyAggregation == meta.getRelationType()) {
                        ReflectUtil.setFieldValue((Object)currentDto, (String)meta.getDtoListName(), (Object)Lists.newArrayList((Object[])new BaseEntityActionDto[]{defaultValueDto}));
                    }
                    if (CollectionUtils.isNotEmpty((Collection)meta.getChildren())) {
                        service.recursiveDefaultValue((EntityMeta)meta, (Object)defaultValueDto);
                    }
                }
            }));
        }
    }

    public List<ExcelImportResultDto> importEntityInitData(ExcelImportTransDto importTransDto) {
        if (log.isInfoEnabled()) {
            log.info("entity:{}", (Object)this.entityMeta.getEntityClass().getName());
        }
        BaseEntityCurdService baseEntityCurdService = this.getBaseEntityCurdService();
        Map uniqueFieldMap = importTransDto.getUniqueFieldMap();
        List dataList = importTransDto.getDataList();
        String entityFullName = importTransDto.getEntityFullName();
        Asserts.isTrue((boolean)this.entityMeta.getEntityClass().getName().equals(entityFullName), (String)"not the same entityFullName");
        try {
            UConsumer & Serializable insertConsumer;
            MultiThreadTransaction.Result result2;
            UConsumer & Serializable updateConsumer;
            MultiThreadTransaction.Result result3;
            List dataDtoList = JsonUtils.toList((String)UdcJsonUtils.toJson((Object)dataList), (Class)((Class)CastUtils.cast((Object)this.entityMeta.getDtoClass())));
            if (CollectionUtils.isEmpty((Collection)dataDtoList)) {
                throw new BusinessException().addError("数据转换错误!");
            }
            AtomicInteger sortNo = new AtomicInteger(0);
            HashMap resultMap = Maps.newHashMapWithExpectedSize((int)dataDtoList.size());
            dataDtoList.stream().forEach(dto -> {
                Integer numNo = sortNo.getAndIncrement();
                dto.setSort_i_no(numNo);
                ExcelImportResultDto resultDto = new ExcelImportResultDto();
                resultDto.setImportSuccessFlag(Boolean.valueOf(true));
                resultMap.put(numNo, resultDto);
            });
            this.uniqueFieldCheck(this.entityMeta, null, dataDtoList, uniqueFieldMap, resultMap);
            boolean errorFlag = resultMap.values().stream().anyMatch(result -> result.getImportSuccessFlag() == false);
            if (errorFlag) {
                return (List)resultMap.values();
            }
            List updateList = dataDtoList.stream().filter(rootDto -> Objects.nonNull(rootDto.getId()) && ActionType.UPDATE == rootDto.getActionType()).collect(Collectors.toList());
            if (CollectionUtils.isNotEmpty(updateList) && !(result3 = this.threadTransaction.executeSplitWithTransaction(updateList, (UConsumer)(updateConsumer = (UConsumer & Serializable)list -> list.stream().forEach(dto -> {
                try {
                    baseEntityCurdService.update(dto);
                }
                catch (Exception e) {
                    Optional.ofNullable(resultMap.get(dto.getSort_i_no())).ifPresent(resultDto -> {
                        resultDto.setImportSuccessFlag(Boolean.valueOf(false));
                        resultDto.setMessage(e.getMessage());
                    });
                    throw e;
                }
            })))).isSuccess()) {
                return (List)resultMap.values();
            }
            List insertList = dataDtoList.stream().filter(rootDto -> Objects.isNull(rootDto.getId()) || ActionType.INSERT == rootDto.getActionType()).collect(Collectors.toList());
            if (CollectionUtils.isNotEmpty(insertList) && !(result2 = this.threadTransaction.executeSplitWithTransaction(insertList, (UConsumer)(insertConsumer = (UConsumer & Serializable)list -> list.stream().forEach(dto -> {
                try {
                    baseEntityCurdService.create(dto);
                }
                catch (Exception e) {
                    Optional.ofNullable(resultMap.get(dto.getSort_i_no())).ifPresent(resultDto -> {
                        resultDto.setImportSuccessFlag(Boolean.valueOf(false));
                        resultDto.setMessage(e.getMessage());
                    });
                    throw e;
                }
            })))).isSuccess()) {
                return (List)resultMap.values();
            }
            return (List)resultMap.values();
        }
        catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private Map<String, String> buildInitDataMap(EntityMeta entityMeta, Collection<? extends BaseEntityActionDto> dtoList) {
        HashMap<String, String> initDataMap = new HashMap<String, String>();
        Map dtoClassMetaMap = EntityMetaUtil.toDtoClassMetaMap((EntityMeta)entityMeta);
        dtoClassMetaMap.forEach((key, meta) -> {
            List subDtoList = dtoList.stream().filter(dto -> key.equals(dto.getClass())).collect(Collectors.toList());
            String entityListJsonStr = UdcJsonUtils.toJson((Object)BeanCopier.copyList(subDtoList, (Class)meta.getEntityClass()));
            initDataMap.put(meta.getEntityClass().getName(), entityListJsonStr);
        });
        return initDataMap;
    }

    private void uniqueFieldCheck(EntityMeta entityMeta, BaseEntityActionDto rootDto, List<D> dataList, Map<String, List<String>> uniqueFieldMap, HashMap<Integer, ExcelImportResultDto> resultMap) {
        if (CollectionUtils.isNotEmpty(dataList)) {
            for (BaseEntityActionDto aggDto : dataList) {
                String value = (String)AnnotationUtils.getAnnotationValue(aggDto.getClass(), DtoInfo.class, (String)"value");
                aggDto.setActionType(ActionType.INSERT);
                List<String> uniqueFieldList = uniqueFieldMap.get(entityMeta.getEntityClass().getName());
                if (CollectionUtils.isNotEmpty(uniqueFieldList)) {
                    BaseEntityCurdService service;
                    List dtoList;
                    HashMap uniqueFieldValueMap = Maps.newHashMapWithExpectedSize((int)uniqueFieldList.size());
                    if (EntityType.SUB_ENTITY == entityMeta.getEntityType()) {
                        uniqueFieldValueMap.put("parentId", aggDto.getId());
                    }
                    for (String fieldName : uniqueFieldList) {
                        Field field = ReflectFieldUtil.getField(aggDto.getClass(), (String)fieldName);
                        if (Objects.isNull(field)) {
                            Optional.ofNullable(resultMap.get(aggDto.getSort_i_no())).ifPresent(resultDto -> {
                                resultDto.setImportSuccessFlag(Boolean.valueOf(false));
                                resultDto.setMessage(value + "唯一标识获取异常！");
                            });
                            break;
                        }
                        uniqueFieldValueMap.put(fieldName, ReflectFieldUtil.getFieldValue((Object)aggDto, (Field)field));
                    }
                    if (CollectionUtils.isNotEmpty((Collection)(dtoList = (service = this.entityBeanContainer.findService(entityMeta.getDtoClass())).selectListByConditions(uniqueFieldValueMap, null)))) {
                        if (dtoList.size() > 1) {
                            if (aggDto instanceof BaseRootDto) {
                                Optional.ofNullable(resultMap.get(aggDto.getSort_i_no())).ifPresent(resultDto -> {
                                    resultDto.setImportSuccessFlag(Boolean.valueOf(false));
                                    resultDto.setMessage(value + "数据不唯一！");
                                });
                            } else if (aggDto instanceof BaseDetailDto && Objects.nonNull(rootDto)) {
                                Optional.ofNullable(resultMap.get(rootDto.getSort_i_no())).ifPresent(resultDto -> {
                                    resultDto.setImportSuccessFlag(Boolean.valueOf(false));
                                    resultDto.setMessage(entityMeta.getDtoListName() + "." + value + "数据不唯一！");
                                });
                            }
                            return;
                        }
                        aggDto.setId(((BaseEntityActionDto)dtoList.get(0)).getId());
                        aggDto.setActionType(ActionType.UPDATE);
                    }
                }
                if (!CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) continue;
                entityMeta.getChildren().stream().forEach(subMeta -> {
                    Object subDtoList = ReflectFieldUtil.getFieldValue((Object)aggDto, (String)subMeta.getDtoListName());
                    if (Objects.nonNull(subDtoList)) {
                        ArrayList dtoColl = Lists.newArrayList();
                        if (subDtoList instanceof Collection) {
                            dtoColl.addAll((Collection)subDtoList);
                        } else {
                            dtoColl.add(subDtoList);
                        }
                        this.uniqueFieldCheck((EntityMeta)subMeta, aggDto, dtoColl, uniqueFieldMap, resultMap);
                    }
                });
            }
            return;
        }
    }

    public PageData<D> dynamicJoinSelect(ProxyJoinParamDto proxyJoinParamDto) {
        if (Objects.isNull(proxyJoinParamDto)) {
            throw BusinessException.message((String)"动态查询条件为空！");
        }
        if (!this.entityMeta.getFullName().endsWith(proxyJoinParamDto.getFromEntity())) {
            throw BusinessException.message((String)("驱动实体设置错误【调用service方法和驱动实体不匹配】" + this.entityMeta.getFullName() + "-" + proxyJoinParamDto.getFromEntity()));
        }
        this.setJdbcDriverIfNecessary(proxyJoinParamDto);
        PageInfo pageInfo = proxyJoinParamDto.getPageInfo();
        boolean needCount = pageInfo.isNeedTotal();
        Integer count = 0;
        if (needCount) {
            SingleResponse countResponse = this.dynamicProxySelectService.dynamicJoinSelectCount(SingleRequest.from((Object)proxyJoinParamDto));
            count = (Integer)ResponseUtils.responseResolve((SingleResponse)countResponse, (String)"dynamicProxySelectService");
        }
        pageInfo.setNeedTotal(false);
        if (this.entityConfig.isEnableLog()) {
            log.info("动态查询条件：{}", (Object)JsonUtils.toJson((Object)proxyJoinParamDto));
        }
        PageResponse pageResponse = this.dynamicProxySelectService.dynamicJoinSelect(SingleRequest.from((Object)proxyJoinParamDto));
        List resultList = ResponseUtils.pageResponseResolve((PageResponse)pageResponse, (String)"dynamicProxySelectService");
        if (this.entityConfig.isEnableLog()) {
            log.info("动态查询结果：{}", (Object)JsonUtils.toJson((Object)resultList));
        }
        PageInfo resultPageInfo = pageResponse.getData().getPageInfo();
        resultPageInfo.setTotal(count.intValue());
        resultPageInfo.setNeedTotal(needCount);
        PageData pageData = new PageData();
        pageData.setPageInfo(resultPageInfo);
        int pages = PageUtil.totalPage((int)count, (int)pageInfo.getPageSize());
        resultPageInfo.setPages(pages);
        pageData.setContent(DbMap2DtoUtil.dbMap2List((EntityMeta)this.entityMeta, (List)proxyJoinParamDto.getEntityList(), (List)resultList));
        return pageData;
    }

    public Integer dynamicCountJoinSelect(ProxyJoinParamDto proxyJoinParamDto) {
        this.setJdbcDriverIfNecessary(proxyJoinParamDto);
        SingleResponse response = this.dynamicProxySelectService.dynamicJoinSelectCount(SingleRequest.from((Object)proxyJoinParamDto));
        if (!response.success()) {
            log.error("筛选方案动态数量查询失败 proxyJoinParam:【{}】 , error: 【{}】", (Object)proxyJoinParamDto, (Object)response.getMessage());
            return 0;
        }
        return (Integer)response.getData().getContent();
    }

    public <D> PageResponse<D> dynamicSelect(ProxyParamDto proxyParamDto) {
        return this.dynamicProxySelectService.dynamicProxySelect(proxyParamDto);
    }

    protected void sendMessage(Serializable message) {
        this.eventBus.publish(message);
    }

    public ResultDto create4Bpm(@Nonnull D frontDto) {
        if (null == frontDto.getId()) {
            frontDto.setId(Ids.gidLong());
        }
        BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
        ApprovalContext context = new ApprovalContext();
        context.putProcessData(frontDto);
        baseEntityCurdService.create4BpmInternal(frontDto, context);
        ResultDto resultDto = new ResultDto();
        HashMap<String, Object> map = new HashMap<String, Object>(2);
        map.put("bpm", context.getParamter("bpm"));
        resultDto.setResultMap(map);
        resultDto.setId(frontDto.getId());
        return resultDto;
    }

    public D create4BpmInternal(D frontDto, ApprovalContext context) {
        BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
        Enum targetStatusType = (Enum)ReflectFieldUtil.getFieldValue(frontDto, (String)"statusType");
        if (Objects.isNull(targetStatusType)) {
            throw BusinessException.message((String)"目标状态错误：目标状态为空");
        }
        if ("PENDING_REVIEW".equals(targetStatusType.name())) {
            log.warn("老表单逻辑：发起走udc，单据状态设置为：TO_BE_SUBMITTED");
            Map enumMap = EnumUtils.getEnumMap((Class)((Class)CastUtils.cast(targetStatusType.getClass())));
            ReflectUtil.setFieldValue(frontDto, (String)"statusType", enumMap.get("TO_BE_SUBMITTED"));
        }
        context.putTargetStatusType(targetStatusType.name());
        this.approvalCallBack.beforeApprovalCreate(context);
        baseEntityCurdService.create(frontDto);
        BaseEntityActionDto oldDto = (BaseEntityActionDto)BeanCopier.copy(frontDto, this.dtoClass, (String[])new String[0]);
        try {
            this.approvalCallBack.afterApprovalCreate(context);
            if (context.hasException()) {
                log.info("数据id{},bpm流程有异常：{},状态置为待提交", (Object)frontDto.getId(), (Object)context.getErrorMsg());
                Map enumMap = EnumUtils.getEnumMap((Class)((Class)CastUtils.cast(targetStatusType.getClass())));
                ReflectUtil.setFieldValue(frontDto, (String)"statusType", enumMap.get("TO_BE_SUBMITTED"));
            }
        }
        catch (Exception e) {
            log.warn("startProcess fail:{}", (Object)frontDto.getId(), (Object)e);
            Map enumMap = EnumUtils.getEnumMap((Class)((Class)CastUtils.cast(targetStatusType.getClass())));
            ReflectUtil.setFieldValue(frontDto, (String)"statusType", enumMap.get("TO_BE_SUBMITTED"));
            this.updateStatusType(frontDto);
            ExceptionUtils.rethrow((Throwable)e);
        }
        if (this.isMainProcess(context)) {
            this.updateRootEntity(oldDto, frontDto);
        }
        return frontDto;
    }

    private boolean isMainProcess(ApprovalContext context) {
        Object processType = context.getParamter("bpmProcessType");
        return processType == null || Boolean.parseBoolean(processType.toString());
    }

    public ResultDto update4Bpm(@Nonnull D frontDto) {
        Enum oldStatus;
        Enum targetStatusType = (Enum)ReflectFieldUtil.getFieldValue(frontDto, (String)"statusType");
        if (Objects.isNull(targetStatusType)) {
            throw BusinessException.message((String)"目标状态错误：目标状态为空");
        }
        boolean checkStatusType = MapUtils.getBoolean((Map)frontDto.getExtendMap(), (Object)"checkStatusType", (Boolean)false);
        Long id = frontDto.getId();
        Asserts.notNull((Object)id, (String)"id");
        boolean callBpm = true;
        if (checkStatusType && Objects.nonNull(oldStatus = this.selectBillStatusById(id))) {
            if (!("NONE".equals(oldStatus.name()) || "DRAFT".equals(oldStatus.name()) || "TO_BE_SUBMITTED".equals(oldStatus.name()))) {
                ReflectUtil.setFieldValue(frontDto, (String)"statusType", null);
                callBpm = false;
                log.warn("表单状态：数据库状态为-{},目标状态为-{},不进行任何bpm操作!", (Object)oldStatus, (Object)targetStatusType);
            } else {
                log.warn("表单状态：数据库状态为-{},目标状态为-{},执行bpm逻辑。", (Object)oldStatus, (Object)targetStatusType);
            }
        }
        ApprovalContext context = new ApprovalContext();
        context.putProcessData(frontDto);
        context.putTargetStatusType(targetStatusType.name());
        if (callBpm) {
            if ("PENDING_REVIEW".equals(targetStatusType.name())) {
                log.warn("老表单逻辑：发起走udc，单据状态设置为：TO_BE_SUBMITTED");
                Map enumMap = EnumUtils.getEnumMap((Class)((Class)CastUtils.cast(targetStatusType.getClass())));
                ReflectUtil.setFieldValue(frontDto, (String)"statusType", enumMap.get("TO_BE_SUBMITTED"));
            }
            this.approvalCallBack.beforeApprovalUpdate(context);
        }
        D dbDto = this.getBaseEntityCurdService().updateWithResult(frontDto);
        BaseEntityActionDto frontCopyDto = (BaseEntityActionDto)BeanCopier.copy(frontDto, this.dtoClass, (String[])new String[0]);
        if (callBpm) {
            try {
                context.putProcessData(frontCopyDto);
                this.approvalCallBack.afterApprovalUpdate(context);
            }
            catch (Exception e) {
                log.warn("startProcess fail:{}", (Object)frontCopyDto.getId(), (Object)e);
                Object statusType = ReflectFieldUtil.getFieldValue((Object)frontCopyDto, (String)"statusType");
                Map enumMap = EnumUtils.getEnumMap((Class)((Class)CastUtils.cast(statusType.getClass())));
                ReflectUtil.setFieldValue((Object)frontCopyDto, (String)"statusType", enumMap.get("TO_BE_SUBMITTED"));
            }
            if (this.isMainProcess(context)) {
                this.updateRootEntity(dbDto, frontCopyDto);
            }
        }
        ResultDto resultDto = new ResultDto();
        HashMap<String, Object> map = new HashMap<String, Object>(2);
        map.put("bpm", context.getParamter("bpm"));
        resultDto.setResultMap(map);
        resultDto.setNums(1);
        resultDto.setId(frontCopyDto.getId());
        return resultDto;
    }

    public D selectCustomCascadeByCondition(QueryConditionDto conditionDto) {
        if (QueryConditionUtil.containsUnderlinedEntities((QueryConditionDto)conditionDto)) {
            Long id = QueryConditionUtil.onlyIdSearch((QueryConditionDto)conditionDto);
            if (Objects.nonNull(id)) {
                return this.getBaseEntityCurdService().selectCascadeById(id);
            }
            throw BusinessException.message((String)"带下划线实体不支持按条件查询！");
        }
        HashMap<String, QueryConditionDto> conditionDtoMap = new HashMap<String, QueryConditionDto>();
        QueryConditionUtil.condition2Map((QueryConditionDto)conditionDto, conditionDtoMap);
        QueryConditionDto queryConditionDto = (QueryConditionDto)conditionDtoMap.get(this.entityMeta.getFullName());
        if (Objects.isNull(queryConditionDto)) {
            throw BusinessException.message((String)"查询不到匹配的实体查询条件");
        }
        D rootDto = this.selectOne2OneCascadeByDyCondition(queryConditionDto);
        if (Objects.isNull(rootDto)) {
            return null;
        }
        List<Long> ids = Arrays.asList(rootDto.getId());
        List<BaseEntityActionDto> rootList = Arrays.asList(rootDto);
        this.recursiveSelectOne2OneCascadeByCondition(this.entityMeta, ids, rootList, conditionDtoMap);
        return rootDto;
    }

    public List<D> selectCustomCascadeListByCondition(QueryConditionDto conditionDto) {
        String entityFullName = this.entityMeta.getFullName();
        String driveEntityFullName = conditionDto.getQueryEntityDto().getEntityFullName();
        if (!driveEntityFullName.equals(entityFullName)) {
            throw BusinessException.message((String)("查询[" + entityFullName + "]服务和驱动实体[" + driveEntityFullName + "]不匹配"));
        }
        HashMap<String, QueryConditionDto> conditionDtoMap = new HashMap<String, QueryConditionDto>();
        QueryConditionUtil.condition2Map((QueryConditionDto)conditionDto, conditionDtoMap);
        QueryConditionDto queryConditionDto = (QueryConditionDto)conditionDtoMap.get(entityFullName);
        if (Objects.isNull(queryConditionDto)) {
            throw BusinessException.message((String)"查询不到匹配的实体查询条件");
        }
        List<D> rootDtoList = this.selectOne2OneCascadeListByDyCondition(queryConditionDto);
        if (CollectionUtils.isEmpty(rootDtoList)) {
            return rootDtoList;
        }
        List<Long> ids = rootDtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
        this.recursiveSelectOne2OneCascadeByCondition(this.entityMeta, ids, rootDtoList, conditionDtoMap);
        return rootDtoList;
    }

    void recursiveSelectOne2OneCascadeByCondition(EntityMeta cEntityMeta, List<Long> parentIds, List<D> rootList, Map<String, QueryConditionDto> conditionDtoMap) {
        if (CollectionUtils.isEmpty(parentIds)) {
            return;
        }
        if (CollectionUtils.isNotEmpty((Collection)cEntityMeta.getChildren())) {
            cEntityMeta.getChildren().stream().filter(item -> RelationType.One2ManyAggregation.equals((Object)item.getRelationType())).filter(item -> conditionDtoMap.containsKey(item.getFullName())).forEach(subMeta -> {
                QueryConditionDto queryConditionDto = (QueryConditionDto)conditionDtoMap.get(subMeta.getFullName());
                if (Objects.isNull(queryConditionDto)) {
                    throw BusinessException.message((String)"查询不到匹配的实体查询条件");
                }
                Optional.ofNullable(this.entityBeanContainer.findService(subMeta.getDtoClass())).ifPresent(subService -> {
                    List<D> subDtoList;
                    String entityName = EntityUtil.getSimpleNameFromFullName((String)subMeta.getFullName());
                    DynamicConditionUtil.addParentId2DynamicCondition((DynamicConditionDto)queryConditionDto.getDynamicConditionDto(), (List)parentIds, (String)entityName);
                    queryConditionDto.getQueryEntityDto().getAttributeName().add("orderNo");
                    Sort sort = queryConditionDto.getSort();
                    if (Objects.isNull(sort)) {
                        sort = Sort.by((String[])new String[]{entityName + "_orderNo"});
                        queryConditionDto.setSort(sort);
                    }
                    if (CollectionUtils.isNotEmpty(subDtoList = subService.selectOne2OneCascadeListByDyCondition(queryConditionDto))) {
                        ArrayListMultimap sonMultimap = ArrayListMultimap.create();
                        subDtoList.forEach(arg_0 -> BaseEntityCurdService.lambda$null$105((Multimap)sonMultimap, arg_0));
                        rootList.forEach(arg_0 -> BaseEntityCurdService.lambda$null$106(subMeta, (Multimap)sonMultimap, arg_0));
                        List<Long> subIds = subDtoList.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                        this.recursiveSelectOne2OneCascadeByCondition((EntityMeta)subMeta, subIds, subDtoList, conditionDtoMap);
                    }
                    if (this.entityConfig.isEnableLog()) {
                        log.info("父dtoList:{},子subDtoList:{}", (Object)JsonUtils.toJson((Object)rootList), (Object)JsonUtils.toJson(subDtoList));
                    }
                });
            });
        }
    }

    public D selectOne2OneCascadeByDyCondition(QueryConditionDto queryConditionDto) {
        PageResponse pageResponse;
        List resultList;
        ProxyJoinParamDto proxyJoinParamDto = DynamicConditionUtil.getProxyJoinParamDto4Query((QueryConditionDto)queryConditionDto);
        this.setJdbcDriverIfNecessary(proxyJoinParamDto);
        PageInfo pageInfo = new PageInfo();
        pageInfo.setNeedTotal(false);
        pageInfo.setPageSize(2);
        proxyJoinParamDto.setPageInfo(pageInfo);
        if (this.entityConfig.isEnableLog()) {
            log.info("单一记录{}查询条件：{}", (Object)queryConditionDto.getQueryEntityDto().getEntityFullName(), (Object)JsonUtils.toJson((Object)proxyJoinParamDto));
        }
        if (CollectionUtils.isEmpty((Collection)(resultList = ResponseUtils.pageResponseResolve((PageResponse)(pageResponse = this.dynamicProxySelectService.dynamicJoinSelect(SingleRequest.from((Object)proxyJoinParamDto))), (String)"dynamicProxySelectService")))) {
            throw new BusinessException("BOOT_4002");
        }
        if (resultList.size() > 1) {
            throw BusinessException.message((String)"查询结果为多条记录");
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("单一记录{}查询结果：{}", (Object)queryConditionDto.getQueryEntityDto().getEntityFullName(), (Object)JsonUtils.toJson((Object)resultList));
        }
        List rootDto = DbMap2DtoUtil.dbMap2List((EntityMeta)this.entityMeta, (List)proxyJoinParamDto.getEntityList(), (List)resultList);
        return (D)((BaseEntityActionDto)rootDto.get(0));
    }

    public List<D> selectOne2OneCascadeListByDyCondition(QueryConditionDto queryConditionDto) {
        PageResponse pageResponse;
        List resultList;
        ProxyJoinParamDto proxyJoinParamDto = DynamicConditionUtil.getProxyJoinParamDto4Query((QueryConditionDto)queryConditionDto);
        this.setJdbcDriverIfNecessary(proxyJoinParamDto);
        if (Objects.isNull(queryConditionDto.getPageInfo())) {
            PageInfo pageInfo = new PageInfo();
            pageInfo.setNeedTotal(false);
            pageInfo.setPageSize(999);
            pageInfo.setPageNumber(1);
            proxyJoinParamDto.setPageInfo(pageInfo);
        } else {
            proxyJoinParamDto.setPageInfo(queryConditionDto.getPageInfo());
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("实体{}查询条件：{}", (Object)queryConditionDto.getQueryEntityDto().getEntityFullName(), (Object)JsonUtils.toJson((Object)proxyJoinParamDto));
        }
        if (CollectionUtils.isEmpty((Collection)(resultList = ResponseUtils.pageResponseResolve((PageResponse)(pageResponse = this.dynamicProxySelectService.dynamicJoinSelect(SingleRequest.from((Object)proxyJoinParamDto))), (String)"dynamicProxySelectService")))) {
            return new ArrayList();
        }
        if (this.entityConfig.isEnableLog()) {
            log.info("实体{}查询结果：{}", (Object)queryConditionDto.getQueryEntityDto().getEntityFullName(), (Object)JsonUtils.toJson((Object)resultList));
        }
        return DbMap2DtoUtil.dbMap2List((EntityMeta)this.entityMeta, (List)proxyJoinParamDto.getEntityList(), (List)resultList);
    }

    public D processingTemplateData(@Nonnull D dto) {
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        return this.recursiveEntityRuntimeData(this.entityMeta, dto, RecursiveType.TEMPLATE);
    }

    public D processingForwardData(@Nonnull D dto) {
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        return this.recursiveEntityRuntimeData(this.entityMeta, dto, RecursiveType.FORWARD);
    }

    private D recursiveEntityRuntimeData(EntityMeta entityMeta, D dto, RecursiveType recursiveType) {
        Class entityClass = entityMeta.getEntityClass();
        List fields = Arrays.stream(entityClass.getDeclaredFields()).filter(f -> f.isAnnotationPresent(EntityAttribute.class)).collect(Collectors.toList());
        Map fieldMap = Arrays.stream(entityMeta.getDtoClass().getDeclaredFields()).filter(f -> f.isAnnotationPresent(DtoAttribute.class)).collect(Collectors.toMap(Field::getName, Function.identity()));
        for (Field field : fields) {
            String fieldDataType = ReflectFieldUtil.getFieldDataType((Field)field);
            UdcDataType dataType = this.commonDataTypes.getDataTypeByName(fieldDataType);
            Field dtoField = (Field)fieldMap.get(field.getName());
            if (dtoField == null) continue;
            Object resValue = null;
            if (RecursiveType.TEMPLATE == recursiveType) {
                resValue = dataType.processingTemplateData(ReflectFieldUtil.getFieldValue(dto, (Field)dtoField));
            } else if (RecursiveType.FORWARD == recursiveType) {
                resValue = dataType.processingForwardData(ReflectFieldUtil.getFieldValue(dto, (Field)dtoField));
            } else {
                throw new BusinessException("不支持的recursiveType类型:" + recursiveType);
            }
            ReflectUtil.setFieldValue(dto, (Field)dtoField, (Object)resValue);
        }
        List childrenMetadatas = entityMeta.getChildren();
        if (CollectionUtils.isNotEmpty((Collection)childrenMetadatas)) {
            childrenMetadatas.forEach(childrenMetadata -> {
                Object childrenData = ReflectFieldUtil.getFieldValue((Object)dto, (String)childrenMetadata.getDtoListName());
                if (Objects.nonNull(childrenData)) {
                    if (childrenData instanceof Collection) {
                        Collection childrenDatas = (Collection)childrenData;
                        if (CollectionUtils.isNotEmpty((Collection)childrenDatas)) {
                            childrenDatas.forEach(data -> this.recursiveEntityRuntimeData((EntityMeta)childrenMetadata, (D)data, recursiveType));
                        }
                    } else {
                        this.recursiveEntityRuntimeData((EntityMeta)childrenMetadata, (D)((BaseEntityActionDto)childrenData), recursiveType);
                    }
                }
            });
        }
        return dto;
    }

    @ECacheEvict
    public ForceUpdateResultDto forceUpdate(@Nonnull D dto) {
        Asserts.isTrue((boolean)this.isMasterEntity, (String)"不允许非聚合根操作");
        log.info("超级管理员修改数据:{}-{},userId:{};ip:{}", new Object[]{this.entityMeta.getCaption(), dto.getId(), RequestContext.get().getUserId(), RequestContext.get().getClientIp()});
        ForceUpdateResultDto resultDto = new ForceUpdateResultDto();
        dto.setActionType(ActionType.UPDATE);
        ArrayList frontDtoList = Lists.newArrayList((Object[])new BaseEntityActionDto[]{dto});
        Map newMap = DtoConvertUtil.defaultUpdateListToMap((EntityMeta)this.entityMeta, (List)frontDtoList);
        D oldDto = this.selectCascadeById(dto.getId());
        if (Objects.isNull(oldDto)) {
            throw new BusinessException("BOOT_4002");
        }
        Map oldMap = DtoConvertUtil.listToMap((EntityMeta)this.entityMeta, (List)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldDto}));
        List newDtoList = DtoConvertUtil.mergeMapData((EntityMeta)this.entityMeta, (Map)oldMap, (Map)newMap);
        int i = this.deleteData(this.entityMeta, newMap, true);
        int j = this.recursiveUpdate(this.entityMeta, newDtoList, oldMap, true);
        BaseEntity entity = (BaseEntity)BeanCopier.copy(dto, this.entityClass, (String[])new String[0]);
        Object mapper = this.getMapper();
        int k = (Integer)EntityClassContext.withEntityClass(mapper, this.entityClass, () -> mapper.update((Object)entity));
        return resultDto;
    }

    private Set<String> getUpdateRootFiled(Object dto) {
        Object caseTitle = ReflectFieldUtil.getFieldValue((Object)dto, (String)"caseTitle");
        if (Objects.isNull(caseTitle)) {
            HashSet<String> set = new HashSet<String>(BillFieldConstant.CASE_FIELD_SETS);
            set.remove("caseTitle");
            return set;
        }
        return BillFieldConstant.CASE_FIELD_SETS;
    }

    private void setJdbcDriverIfNecessary(ProxyJoinParamDto proxyJoinParamDto) {
        if (this.getClass().getClassLoader() instanceof ModuleAppClassLoader) {
            log.info("动态查询：使用jdbc 直接查询数据");
            proxyJoinParamDto.setJdbcDriver(Boolean.valueOf(true));
        }
    }

    private void printTransactionInfo() {
        String transactionName = TransactionSynchronizationManager.getCurrentTransactionName();
        Integer isolationLevel = TransactionSynchronizationManager.getCurrentTransactionIsolationLevel();
        Boolean active = TransactionSynchronizationManager.isActualTransactionActive();
        log.info("事务名称：{},事务级别:{},事务状态：{}", new Object[]{transactionName, isolationLevel, active});
    }

    public Class<?> getEntityClass() {
        return this.entityClass;
    }

    public EntityMeta getEntityMeta() {
        return this.entityMeta;
    }

    private static /* synthetic */ void lambda$null$106(EntityMeta subMeta, Multimap sonMultimap, BaseEntityActionDto dto) {
        Field field = ReflectFieldUtil.getField(dto.getClass(), (String)subMeta.getDtoListName());
        if (field != null) {
            Collection sonDtolist = sonMultimap.get((Object)dto.getId());
            if (CollectionUtils.isNotEmpty((Collection)sonDtolist) && RelationType.One2ManyAggregation == subMeta.getRelationType()) {
                ReflectUtil.setFieldValue((Object)dto, (Field)field, (Object)sonDtolist);
            }
        } else {
            String error = String.format("Dto[%s]找不到子表属性:%s", dto.getClass(), subMeta.getDtoListName());
            throw BusinessException.message((String)error);
        }
    }

    private static /* synthetic */ void lambda$null$105(Multimap sonMultimap, BaseEntityActionDto dto) {
        Object parentId = ReflectFieldUtil.getFieldValue((Object)dto, (String)"parentId");
        if (!Objects.nonNull(parentId)) {
            String error = String.format("Dto[%s]找不到parentId属性", dto.getClass().toString());
            throw BusinessException.message((String)error);
        }
        sonMultimap.put((Object)((Long)parentId), (Object)dto);
    }

    private /* synthetic */ void lambda$handleSubRelation$64(List subDtoList, Supplier supplier, List subIds, EntityMeta sonMeta) {
        BaseEntityCurdService sonService = this.entityBeanContainer.findService(sonMeta.getDtoClass());
        if (RelationType.One2OneAggregation == sonMeta.getRelationType()) {
            subDtoList.stream().forEach(arg_0 -> BaseEntityCurdService.lambda$null$63(sonService, sonMeta, (Supplier)supplier, arg_0));
        } else if (RelationType.One2ManyAggregation == sonMeta.getRelationType()) {
            sonService.setMultiSubDtoList(subIds, subDtoList, sonMeta, supplier);
        }
    }

    private static /* synthetic */ void lambda$null$63(BaseEntityCurdService sonService, EntityMeta sonMeta, Supplier supplier, BaseEntityActionDto dto) {
        sonService.setSingeSubDtoList(dto.getId(), dto, sonMeta, supplier);
    }

    private static /* synthetic */ void lambda$null$61(EntityMeta subMeta, Multimap sonMultimap, BaseEntityActionDto dto) {
        Collection sonDtolist;
        Field field = ReflectFieldUtil.getField(dto.getClass(), (String)subMeta.getDtoListName());
        if (field != null && CollectionUtils.isNotEmpty((Collection)(sonDtolist = sonMultimap.get((Object)dto.getId())))) {
            if (RelationType.One2OneAggregation == subMeta.getRelationType()) {
                ReflectUtil.setFieldValue((Object)dto, (Field)field, sonDtolist.iterator().next());
            } else if (RelationType.One2ManyAggregation == subMeta.getRelationType()) {
                sonDtolist = sonDtolist.stream().sorted(Comparator.comparing(d -> ((BaseDetailDto)d).getOrderNo(), Comparator.nullsLast(Integer::compareTo))).collect(Collectors.toList());
                ReflectUtil.setFieldValue((Object)dto, (Field)field, (Object)sonDtolist);
            }
        }
    }

    private static /* synthetic */ void lambda$null$59(Multimap sonMultimap, BaseEntityActionDto dto) {
        Object parentId = ReflectFieldUtil.getFieldValue((Object)dto, (String)"parentId");
        if (Objects.nonNull(parentId)) {
            sonMultimap.put((Object)((Long)parentId), (Object)dto);
        }
    }
}
