/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.collection.IterUtil
 *  cn.hutool.core.convert.Convert
 *  cn.hutool.core.map.MapUtil
 *  cn.hutool.core.util.ArrayUtil
 *  cn.hutool.core.util.ObjectUtil
 *  cn.hutool.core.util.ReflectUtil
 *  cn.hutool.core.util.StrUtil
 *  com.google.common.collect.Lists
 *  com.google.common.collect.Sets
 *  com.seeyon.boot.annotation.enums.RelationType
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.context.RequestContext
 *  com.seeyon.boot.enums.ActionType
 *  com.seeyon.boot.enums.DataType
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.lowcode.core.AttributeMeta
 *  com.seeyon.boot.starter.lowcode.core.EntityMeta
 *  com.seeyon.boot.starter.lowcode.dto.AggEntityChangeDto
 *  com.seeyon.boot.starter.lowcode.dto.AttributeChangeDto
 *  com.seeyon.boot.starter.lowcode.dto.EntityChangeDto
 *  com.seeyon.boot.starter.lowcode.enums.FlowActionType
 *  com.seeyon.boot.starter.lowcode.util.DtoConvertUtil
 *  com.seeyon.boot.starter.lowcode.util.EntityMetaUtil
 *  com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil
 *  com.seeyon.boot.util.DateUtils
 *  com.seeyon.boot.util.StringUtils
 *  com.seeyon.boot.util.id.Ids
 *  com.seeyon.ctp.metadata.domain.service.MetadataService
 *  com.seeyon.ctp.metadata.dto.model.MaskableDto
 *  com.seeyon.ctp.metadata.enums.MetadataTypeEnum
 *  com.seeyon.udc.common.constant.UdcCommonConstant
 *  com.seeyon.udc.common.dto.BaseDetailDto
 *  com.seeyon.udc.common.dto.BaseEntityActionDto
 *  com.seeyon.udc.common.dto.BaseRootDto
 *  com.seeyon.udc.common.utils.AppNameUtil
 *  org.apache.commons.collections.CollectionUtils
 *  org.apache.commons.collections.MapUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.seeyon.boot.starter.lowcode.helper;

import cn.hutool.core.collection.IterUtil;
import cn.hutool.core.convert.Convert;
import cn.hutool.core.map.MapUtil;
import cn.hutool.core.util.ArrayUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.ReflectUtil;
import cn.hutool.core.util.StrUtil;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.seeyon.boot.annotation.enums.RelationType;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.context.RequestContext;
import com.seeyon.boot.enums.ActionType;
import com.seeyon.boot.enums.DataType;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.lowcode.core.AttributeMeta;
import com.seeyon.boot.starter.lowcode.core.EntityMeta;
import com.seeyon.boot.starter.lowcode.dto.AggEntityChangeDto;
import com.seeyon.boot.starter.lowcode.dto.AttributeChangeDto;
import com.seeyon.boot.starter.lowcode.dto.EntityChangeDto;
import com.seeyon.boot.starter.lowcode.enums.FlowActionType;
import com.seeyon.boot.starter.lowcode.util.DtoConvertUtil;
import com.seeyon.boot.starter.lowcode.util.EntityMetaUtil;
import com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil;
import com.seeyon.boot.util.DateUtils;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.boot.util.id.Ids;
import com.seeyon.ctp.metadata.domain.service.MetadataService;
import com.seeyon.ctp.metadata.dto.model.MaskableDto;
import com.seeyon.ctp.metadata.enums.MetadataTypeEnum;
import com.seeyon.udc.common.constant.UdcCommonConstant;
import com.seeyon.udc.common.dto.BaseDetailDto;
import com.seeyon.udc.common.dto.BaseEntityActionDto;
import com.seeyon.udc.common.dto.BaseRootDto;
import com.seeyon.udc.common.utils.AppNameUtil;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.MapUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DtoFieldHelper {
    private static final Logger log = LoggerFactory.getLogger(DtoFieldHelper.class);
    private static Set<String> IGNORE_FIELDS = Sets.newHashSet((Object[])new String[]{"createTime", "creator", "creatorInstitution", "creatorDepartment", "creatorPost", "updater", "updateTime", "secretN", "deductionInfo", "orderNo", "treePath", "isLeaf", "treeLevel", "treeCaptionPath", "id", "validate", "maskTypeMap", "positionIndex", "linkSourceIds", "extendMap", "errorInfoList", "maskTypeMap", "__key", "version", "sort_i_no", "draft"});

    public static final <D extends BaseEntityActionDto> D throwActionTypeIfAbsent(D dto) {
        if (Objects.nonNull(dto) && Objects.isNull(dto.getActionType())) {
            throw new BusinessException().addError("actionType cannot be null");
        }
        if (ActionType.UPDATE == dto.getActionType() && Objects.isNull(dto.getId())) {
            throw new BusinessException().addError("actionType is update,id cannot be null");
        }
        return dto;
    }

    public static final <D extends BaseEntityActionDto> D setIdIfAbsent(D dto) {
        if (Objects.nonNull(dto) && (Objects.isNull(dto.getId()) || Objects.equals(UdcCommonConstant.NULL_ID, dto.getId()))) {
            dto.setId(Ids.gidLong());
        }
        return dto;
    }

    public static final <D extends BaseEntityActionDto> List<D> setParentIdIfAbsent(D parentDto, List<D> dtoList) {
        if (Objects.nonNull(parentDto) && Objects.nonNull(parentDto.getId()) && CollectionUtils.isNotEmpty(dtoList)) {
            Long parentId = parentDto.getId();
            ActionType parentActionType = parentDto.getActionType();
            dtoList.stream().forEach(dto -> {
                DtoFieldHelper.setIdIfAbsent(dto);
                if (dto instanceof BaseDetailDto) {
                    Object subParentIdObj = ReflectFieldUtil.getFieldValue((Object)dto, (String)"parentId");
                    if (Objects.isNull(subParentIdObj) || Objects.equals(UdcCommonConstant.NULL_ID, subParentIdObj)) {
                        ReflectUtil.setFieldValue((Object)dto, (String)"parentId", (Object)parentId);
                    } else if (!Objects.equals(parentId, subParentIdObj)) {
                        ReflectUtil.setFieldValue((Object)dto, (String)"parentId", (Object)parentId);
                    }
                }
                if (ActionType.INSERT.equals((Object)parentActionType)) {
                    dto.setActionType(ActionType.INSERT);
                }
            });
        }
        return dtoList;
    }

    public static final <D extends BaseEntityActionDto> D setActionTypeIfAbsent(D dto, ActionType actionType) {
        if (Objects.nonNull(dto) && Objects.isNull(dto.getActionType())) {
            dto.setActionType(actionType);
        }
        return dto;
    }

    public static final <D extends BaseEntityActionDto> D setActionType(D dto, ActionType actionType) {
        if (Objects.nonNull(dto)) {
            dto.setActionType(actionType);
        }
        return dto;
    }

    public static final <D extends BaseEntityActionDto> D resetInsert(D parentDto, D subDto) {
        if (Objects.nonNull(parentDto)) {
            parentDto.setActionType(ActionType.INSERT);
            if (Objects.isNull(parentDto.getId()) || Objects.equals(UdcCommonConstant.NULL_ID, parentDto.getId())) {
                parentDto.setId(Ids.gidLong());
            }
            if (Objects.isNull(parentDto.getDraft())) {
                parentDto.setDraft(Boolean.valueOf(false));
            }
            if (Objects.isNull(parentDto.getCreateTime())) {
                parentDto.setCreateTime(new Date());
            }
            if (Objects.isNull(parentDto.getUpdateTime())) {
                parentDto.setUpdateTime(new Date());
            }
        }
        if (Objects.nonNull(parentDto) && Objects.nonNull(subDto)) {
            subDto.setActionType(ActionType.INSERT);
            if (Objects.isNull(subDto.getId()) || Objects.equals(UdcCommonConstant.NULL_ID, subDto.getId())) {
                subDto.setId(Ids.gidLong());
            }
            if (parentDto.getDraft().booleanValue()) {
                subDto.setDraft(parentDto.getDraft());
            }
            if (Objects.isNull(subDto.getCreateTime())) {
                subDto.setCreateTime(new Date());
            }
            if (Objects.isNull(subDto.getUpdateTime())) {
                subDto.setUpdateTime(new Date());
            }
            if (Objects.nonNull(parentDto) && subDto instanceof BaseDetailDto) {
                Object parentIdObj = ReflectFieldUtil.getFieldValue(subDto, (String)"parentId");
                if (Objects.isNull(parentIdObj) || Objects.equals(UdcCommonConstant.NULL_ID, parentIdObj)) {
                    ReflectUtil.setFieldValue(subDto, (String)"parentId", (Object)parentDto.getId());
                } else if (!Objects.equals(parentDto.getId(), parentIdObj)) {
                    subDto.setId(Ids.gidLong());
                    ReflectUtil.setFieldValue(subDto, (String)"parentId", (Object)parentDto.getId());
                }
            }
        }
        return subDto;
    }

    public static final <D extends BaseEntityActionDto> D resetChildNormal(D parentDto) {
        if (Objects.nonNull(parentDto) && parentDto instanceof BaseDetailDto) {
            parentDto.setActionType(ActionType.NORMAL);
        }
        return parentDto;
    }

    public static final <D extends BaseEntityActionDto> D resetId(D parentDto, D subDto) {
        if (Objects.nonNull(parentDto)) {
            parentDto.setActionType(ActionType.INSERT);
            parentDto.setId(Ids.gidLong());
            if (Objects.isNull(parentDto.getDraft())) {
                parentDto.setDraft(Boolean.valueOf(false));
            }
        }
        if (Objects.nonNull(parentDto) && Objects.nonNull(subDto)) {
            Field field;
            subDto.setActionType(ActionType.INSERT);
            subDto.setId(Ids.gidLong());
            subDto.setDraft(parentDto.getDraft());
            if (Objects.nonNull(parentDto) && subDto instanceof BaseDetailDto && Objects.nonNull(field = ReflectFieldUtil.getField(subDto.getClass(), (String)"parentId"))) {
                ReflectUtil.setFieldValue(subDto, (Field)field, (Object)parentDto.getId());
            }
        }
        return subDto;
    }

    public static final <D extends BaseEntityActionDto> void set1ToNDtoList(D parentDto, EntityMeta entityMeta, List<D> mergedSubDtoList) {
        if (Objects.nonNull(parentDto) && Objects.nonNull(entityMeta)) {
            Field field;
            if (RelationType.One2OneAggregation == entityMeta.getRelationType()) {
                Object fieldValue = CollectionUtils.isNotEmpty(mergedSubDtoList) ? mergedSubDtoList.get(0) : null;
                Field field2 = ReflectFieldUtil.getField(parentDto, (String)entityMeta.getDtoListName());
                if (Objects.nonNull(field2)) {
                    ReflectFieldUtil.setFieldValue(parentDto, (Field)field2, fieldValue);
                }
            } else if (RelationType.One2ManyAggregation == entityMeta.getRelationType() && Objects.nonNull(field = ReflectFieldUtil.getField(parentDto, (String)entityMeta.getDtoListName()))) {
                ReflectFieldUtil.setFieldValue(parentDto, (Field)field, mergedSubDtoList);
            }
        }
    }

    public static <D extends BaseEntityActionDto> void setSubEntityOrderNo(EntityMeta entityMeta, List<D> dtoList) {
        Optional<BaseEntityActionDto> optional;
        if (Objects.nonNull(entityMeta) && entityMeta.isSortField() && CollectionUtils.isNotEmpty(dtoList) && (optional = dtoList.stream().filter(item -> {
            Object orderNo = ReflectFieldUtil.getFieldValue((Object)item, (String)"orderNo");
            return Objects.isNull(orderNo) || orderNo.equals(0);
        }).findAny()).isPresent()) {
            for (int i = 0; i < dtoList.size(); ++i) {
                ReflectUtil.setFieldValue(dtoList.get(i), (String)"orderNo", (Object)((i + 1) * 10000));
            }
        }
    }

    public static <D extends BaseEntityActionDto> List<AggEntityChangeDto> diffDataByList(EntityMeta entityMeta, List<D> oldDtoList, List<D> newDtoList) {
        ArrayList<AggEntityChangeDto> aggEntityChangeList = new ArrayList<AggEntityChangeDto>();
        Map<Object, Object> aggOldDtoMap = CollectionUtils.isEmpty(oldDtoList) ? Collections.emptyMap() : oldDtoList.stream().collect(Collectors.toMap(BaseEntityActionDto::getId, item -> item, (o1, o2) -> o1));
        Map<Long, BaseEntityActionDto> aggNewDtoMap = CollectionUtils.isEmpty(newDtoList) ? Collections.emptyMap() : newDtoList.stream().collect(Collectors.toMap(BaseEntityActionDto::getId, item -> item, (o1, o2) -> o1));
        aggNewDtoMap.forEach((rootId, newRootDto) -> {
            boolean haveChange;
            Map newMap = DtoConvertUtil.listToMap((EntityMeta)entityMeta, (List)Lists.newArrayList((Object[])new BaseEntityActionDto[]{newRootDto}));
            BaseEntityActionDto oldRootDto = (BaseEntityActionDto)aggOldDtoMap.get(rootId);
            Map oldMap = Objects.nonNull(oldRootDto) ? DtoConvertUtil.listToMap((EntityMeta)entityMeta, (List)Lists.newArrayList((Object[])new BaseEntityActionDto[]{oldRootDto})) : Collections.emptyMap();
            List<EntityChangeDto> entityChangeList = DtoFieldHelper.diffDataByMap(entityMeta, oldMap, newMap);
            if (CollectionUtils.isNotEmpty(entityChangeList) && (haveChange = entityChangeList.stream().anyMatch(item -> CollectionUtils.isNotEmpty((Collection)item.getAttrChangeList())))) {
                AggEntityChangeDto aggEntityChangeDto = new AggEntityChangeDto();
                aggEntityChangeDto.setDataId(rootId);
                if (newRootDto instanceof BaseRootDto) {
                    FlowActionType flowActionType = Optional.ofNullable(((BaseRootDto)newRootDto).getExtraParamMap()).map(map -> FlowActionType.valueOf((String)MapUtils.getString((Map)map, (Object)"operationType", (String)FlowActionType.NONE.name()))).orElse(FlowActionType.NONE);
                    aggEntityChangeDto.setFlowActionType(flowActionType);
                }
                aggEntityChangeDto.setActionType(newRootDto.getActionType());
                aggEntityChangeDto.setEntityFullName(entityMeta.getFullName());
                aggEntityChangeDto.setEntityCaption(entityMeta.getCaption());
                aggEntityChangeDto.setOperatorId(RequestContext.get().getUserId());
                aggEntityChangeDto.setEntityChangeList(entityChangeList);
                aggEntityChangeList.add(aggEntityChangeDto);
            }
        });
        return aggEntityChangeList;
    }

    public static <D extends BaseEntityActionDto> List<EntityChangeDto> diffDataByMap(EntityMeta entityMeta, Map<Long, D> oldMap, Map<Long, D> newMap) {
        ArrayList<EntityChangeDto> entityChangeList = new ArrayList<EntityChangeDto>();
        Map metaMap = EntityMetaUtil.toDtoClassMetaMap((EntityMeta)entityMeta);
        newMap.forEach((id, newDto) -> Optional.ofNullable(metaMap.get(newDto.getClass())).ifPresent(meta -> {
            Object parentId;
            EntityChangeDto entityChangeDto = new EntityChangeDto();
            Long rootId = newDto.getId();
            ActionType actionType = newDto.getActionType();
            entityChangeDto.setActionType(actionType);
            entityChangeDto.setDataId(rootId);
            entityChangeDto.setOperatorId(RequestContext.get().getUserId());
            if (newDto instanceof BaseDetailDto && Objects.nonNull(parentId = ReflectFieldUtil.getFieldValue((Object)newDto, (String)"parentId"))) {
                entityChangeDto.setParentId(Convert.toLong((Object)parentId, (Long)0L));
            }
            entityChangeDto.setRelationType(meta.getRelationType());
            entityChangeDto.setEntityFullName(meta.getFullName());
            entityChangeDto.setEntityCaption(meta.getCaption());
            List<AttributeChangeDto> attributeChangeList = DtoFieldHelper.extractAttrChange(meta, (BaseEntityActionDto)oldMap.get(rootId), newDto);
            entityChangeDto.setAttrChangeList(attributeChangeList);
            entityChangeList.add(entityChangeDto);
        }));
        return entityChangeList;
    }

    private static <D extends BaseEntityActionDto> List<AttributeChangeDto> extractAttrChange(EntityMeta entityMeta, D oldDto, D newDto) {
        return DtoFieldHelper.extractAttrChange(entityMeta, oldDto, newDto, IGNORE_FIELDS);
    }

    private static boolean isContentField(AttributeMeta attributeMeta) {
        boolean isContentField;
        boolean bl = isContentField = Objects.nonNull(attributeMeta) && "CONTENT".equals(attributeMeta.getRealDataType());
        if (isContentField) {
            log.info("realDataType:{},fullName:{}", (Object)attributeMeta.getRealDataType(), (Object)attributeMeta.getFullName());
        }
        return isContentField;
    }

    private static <D extends BaseEntityActionDto> List<AttributeChangeDto> extractAttrChange(EntityMeta entityMeta, D oldDto, D newDto, Set<String> ignoreFields) {
        Predicate<Field> enableExtFieldFilter;
        ArrayList<AttributeChangeDto> attributeChangeList = new ArrayList<AttributeChangeDto>();
        ActionType actionType = newDto.getActionType();
        Field[] fields = ReflectUtil.getFields(newDto.getClass());
        Map<String, AttributeMeta> attributeMap = entityMeta.getAttributes().stream().collect(Collectors.toMap(AttributeMeta::getName, attributeMeta -> attributeMeta));
        Predicate<Field> ignoreFieldsFilter = field -> CollectionUtils.isEmpty((Collection)ignoreFields) || !ignoreFields.contains(field.getName());
        Predicate<Field> contentFieldFilter = field -> {
            AttributeMeta attributeMeta = (AttributeMeta)attributeMap.get(field.getName());
            return !DtoFieldHelper.isContentField(attributeMeta);
        };
        boolean extEntity = StringUtils.equals((String)"EXT", (String)entityMeta.getEntityCategory());
        if (extEntity) {
            List<String> listEnableExtField = DtoFieldHelper.listEnableExtField(entityMeta);
            enableExtFieldFilter = field -> listEnableExtField.contains(field.getName());
        } else {
            enableExtFieldFilter = field -> true;
        }
        Predicate<Field> filterChain = ignoreFieldsFilter.and(contentFieldFilter).and(enableExtFieldFilter);
        Arrays.stream(fields).filter(filterChain).forEach(field -> {
            AttributeChangeDto changeDto = new AttributeChangeDto();
            AttributeMeta attributeMeta = (AttributeMeta)attributeMap.get(field.getName());
            if (Objects.nonNull(attributeMeta)) {
                changeDto.setName(attributeMeta.getName());
                if (Objects.nonNull(attributeMeta.getMaskType())) {
                    MaskableDto maskableInfo = new MaskableDto();
                    maskableInfo.setType(attributeMeta.getMaskType().type().name());
                    maskableInfo.setMaskKeys(attributeMeta.getMaskType().maskKeys());
                    maskableInfo.setStart(attributeMeta.getMaskType().start());
                    maskableInfo.setEnd(attributeMeta.getMaskType().end());
                    changeDto.setMaskable(maskableInfo);
                }
                if (ActionType.INSERT == actionType) {
                    Object value = ReflectFieldUtil.getFieldValue((Object)newDto, (Field)field);
                    if (!DtoFieldHelper.isEmptyOrZero(value)) {
                        changeDto.setNewValue(value);
                        attributeChangeList.add(changeDto);
                    }
                } else if (ActionType.DELETE == actionType) {
                    Optional.ofNullable(oldDto).ifPresent(d -> {
                        Object oldValue = ReflectFieldUtil.getFieldValue((Object)oldDto, (Field)field);
                        if (!DtoFieldHelper.isEmptyOrZero(oldValue)) {
                            changeDto.setOldValue(oldValue);
                            attributeChangeList.add(changeDto);
                        }
                    });
                } else if (ActionType.UPDATE == actionType) {
                    Object oldValue = ReflectFieldUtil.getFieldValue((Object)oldDto, (Field)field);
                    Object newValue = ReflectFieldUtil.getFieldValue((Object)newDto, (Field)field);
                    if (DataType.DATE.name().equals(attributeMeta.getDataType())) {
                        if (Objects.nonNull(oldValue)) {
                            oldValue = DateUtils.getDate((Date)((Date)oldValue));
                        }
                        if (Objects.nonNull(newValue)) {
                            newValue = DateUtils.getDate((Date)((Date)newValue));
                        }
                    }
                    boolean isCleanField = false;
                    List emptyFields = newDto.get__emptyFields();
                    if (CollectionUtils.isNotEmpty((Collection)emptyFields)) {
                        isCleanField = emptyFields.contains(field.getName());
                    }
                    if (!DtoFieldHelper.isEmpty(newValue) || isCleanField) {
                        if (List.class.isAssignableFrom(field.getType())) {
                            if (newValue instanceof Collection && oldValue instanceof Collection) {
                                Collection r = CollectionUtils.disjunction((Collection)((Collection)newValue), (Collection)((Collection)oldValue));
                                if (CollectionUtils.isNotEmpty((Collection)r)) {
                                    changeDto.setOldValue(oldValue);
                                    changeDto.setNewValue(newValue);
                                    attributeChangeList.add(changeDto);
                                }
                            } else {
                                changeDto.setOldValue(oldValue);
                                changeDto.setNewValue(newValue);
                                attributeChangeList.add(changeDto);
                            }
                        } else if (!ObjectUtil.equals((Object)newValue, (Object)oldValue)) {
                            changeDto.setNewValue(newValue);
                            changeDto.setOldValue(oldValue);
                            attributeChangeList.add(changeDto);
                        }
                    }
                }
            }
        });
        return attributeChangeList;
    }

    private static boolean isEmptyOrZero(Object obj) {
        if (null == obj) {
            return true;
        }
        if (obj instanceof Long) {
            return (Long)obj == 0L;
        }
        if (obj instanceof Enum) {
            return "NONE".equals(((Enum)obj).name());
        }
        if (obj instanceof CharSequence) {
            return StrUtil.isEmpty((CharSequence)((CharSequence)obj));
        }
        if (obj instanceof Map) {
            return MapUtil.isEmpty((Map)((Map)obj));
        }
        if (obj instanceof Iterable) {
            return IterUtil.isEmpty((Iterable)((Iterable)obj));
        }
        if (obj instanceof Iterator) {
            return IterUtil.isEmpty((Iterator)((Iterator)obj));
        }
        if (ArrayUtil.isArray((Object)obj)) {
            return ArrayUtil.isEmpty((Object)obj);
        }
        return false;
    }

    private static boolean isEmpty(Object obj) {
        if (null == obj) {
            return true;
        }
        if (obj instanceof CharSequence) {
            return Objects.isNull(obj);
        }
        if (obj instanceof Map) {
            return MapUtil.isEmpty((Map)((Map)obj));
        }
        if (obj instanceof Iterable) {
            return IterUtil.isEmpty((Iterable)((Iterable)obj));
        }
        if (obj instanceof Iterator) {
            return IterUtil.isEmpty((Iterator)((Iterator)obj));
        }
        if (ArrayUtil.isArray((Object)obj)) {
            return ArrayUtil.isEmpty((Object)obj);
        }
        return false;
    }

    private static List<String> listEnableExtField(EntityMeta entityMeta) {
        String appName;
        MetadataService metadataService;
        List list;
        ArrayList<String> extEnableList = new ArrayList<String>();
        if (StringUtils.equals((String)"EXT", (String)entityMeta.getEntityCategory()) && CollectionUtils.isNotEmpty((Collection)(list = (metadataService = (MetadataService)Apps.getBeanFactory().getBean(MetadataService.class)).select(MetadataTypeEnum.Entity, appName = AppNameUtil.getAppNameByEntityFullName((String)entityMeta.getFullName()))))) {
            list.stream().filter(entityMetadataDto -> StringUtils.equals((String)entityMetadataDto.getFullName(), (String)entityMeta.getFullName())).forEach(entityMetadataDto -> {
                Map attributesMap = entityMetadataDto.getAttributes();
                if (MapUtils.isNotEmpty((Map)attributesMap)) {
                    attributesMap.forEach((name, attr) -> {
                        if (StringUtils.isNotBlank((CharSequence)attr.getCaption())) {
                            extEnableList.add((String)name);
                        }
                    });
                }
            });
            return extEnableList;
        }
        return Collections.emptyList();
    }

    static {
        IGNORE_FIELDS.add("sendState");
        IGNORE_FIELDS.add("parentId");
        IGNORE_FIELDS.add("statusType");
        IGNORE_FIELDS.add("caseSendTime");
        IGNORE_FIELDS.add("caseSender");
        IGNORE_FIELDS.add("caseSenderInstitution");
        IGNORE_FIELDS.add("caseSenderDepartment");
        IGNORE_FIELDS.add("caseSenderPost");
        IGNORE_FIELDS.add("templateId");
        IGNORE_FIELDS.add("caseId");
        IGNORE_FIELDS.add("caseTitle");
        IGNORE_FIELDS.add("terminatorId");
        IGNORE_FIELDS.add("terminateTime");
        IGNORE_FIELDS.add("terminateReason");
        IGNORE_FIELDS.add("terminateStatusType");
        IGNORE_FIELDS.add("cancelTerminatorId");
        IGNORE_FIELDS.add("cancelTerminateTime");
        IGNORE_FIELDS.add("cancelTerminateReason");
        IGNORE_FIELDS.add("nullifyId");
        IGNORE_FIELDS.add("nullifyTime");
        IGNORE_FIELDS.add("nullifyReason");
        IGNORE_FIELDS.add("nullifyStatusType");
        IGNORE_FIELDS.add("cancelNullifyId");
        IGNORE_FIELDS.add("cancelNullifyTime");
        IGNORE_FIELDS.add("cancelNullifyReason");
        IGNORE_FIELDS.add("suspenderId");
        IGNORE_FIELDS.add("suspendTime");
        IGNORE_FIELDS.add("suspendReason");
        IGNORE_FIELDS.add("suspendStatusType");
        IGNORE_FIELDS.add("cancelSuspenderId");
        IGNORE_FIELDS.add("cancelSuspendTime");
        IGNORE_FIELDS.add("cancelSuspendReason");
    }
}
