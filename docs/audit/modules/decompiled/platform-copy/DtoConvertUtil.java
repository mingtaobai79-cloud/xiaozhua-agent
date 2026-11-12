/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.lang.Pair
 *  cn.hutool.core.util.ReflectUtil
 *  com.google.common.collect.Lists
 *  com.google.common.collect.Maps
 *  com.google.common.collect.Sets
 *  com.google.common.collect.Sets$SetView
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.enums.ActionType
 *  com.seeyon.boot.enums.DataType
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.lowcode.core.EntityMeta
 *  com.seeyon.boot.starter.lowcode.helper.DtoFieldHelper
 *  com.seeyon.boot.starter.lowcode.util.EntityMetaUtil
 *  com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil
 *  com.seeyon.boot.util.Asserts
 *  com.seeyon.udc.common.dto.BaseDetailDto
 *  com.seeyon.udc.common.dto.BaseEntityActionDto
 *  com.seeyon.udc.common.utils.AnnotationUtils
 *  org.apache.commons.collections4.CollectionUtils
 *  org.apache.commons.collections4.MapUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.data.util.CastUtils
 */
package com.seeyon.boot.starter.lowcode.util;

import cn.hutool.core.lang.Pair;
import cn.hutool.core.util.ReflectUtil;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.enums.ActionType;
import com.seeyon.boot.enums.DataType;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.lowcode.core.EntityMeta;
import com.seeyon.boot.starter.lowcode.helper.DtoFieldHelper;
import com.seeyon.boot.starter.lowcode.util.EntityMetaUtil;
import com.seeyon.boot.starter.lowcode.util.ReflectFieldUtil;
import com.seeyon.boot.util.Asserts;
import com.seeyon.udc.common.dto.BaseDetailDto;
import com.seeyon.udc.common.dto.BaseEntityActionDto;
import com.seeyon.udc.common.utils.AnnotationUtils;
import java.lang.reflect.AnnotatedElement;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.collections4.MapUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.util.CastUtils;

public class DtoConvertUtil {
    private static final Logger log = LoggerFactory.getLogger(DtoConvertUtil.class);
    private static final Set<String> ingoreFields = Sets.newHashSet((Object[])new String[]{"updateTime", "createTime"});
    private static final Set<String> ENABLED_NULL_FIELD_TYPE = Sets.newHashSet((Object[])new String[]{DataType.INTEGER.name(), DataType.DECIMAL.name(), DataType.CURRENCY.name(), DataType.DATE.name(), DataType.DATETIME.name()});
    private static final Set<String> CAN_NOT_SET_NULL_FIELDS = Sets.newHashSet((Object[])new String[]{"version", "createTime", "updateTime", "caseSendTime", "orderNo", "terminateTime", "cancelTerminateTime", "nullifyTime", "cancelNullifyTime", "suspendTime", "cancelSuspendTime", "billDate"});

    public static <DTO extends BaseEntityActionDto, T> DTO setValueHandle(EntityMeta entityMeta, DTO dto, Supplier<T> t, BiConsumer<DTO, T> callback) {
        if (Objects.isNull(dto)) {
            return null;
        }
        if (callback != null) {
            callback.accept(dto, (DTO)t.get());
        }
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            entityMeta.getChildren().stream().forEach(meta -> {
                Object dtoList = ReflectFieldUtil.getFieldValue((Object)dto, (String)meta.getDtoListName());
                if (Objects.nonNull(dtoList)) {
                    ArrayList dtoColl = Lists.newArrayList();
                    if (dtoList instanceof Collection) {
                        dtoColl.addAll((Collection)CastUtils.cast((Object)dtoList));
                    } else {
                        dtoColl.add(CastUtils.cast((Object)dtoList));
                    }
                    dtoColl.forEach(arg_0 -> DtoConvertUtil.lambda$null$0(meta, (Supplier)t, callback, arg_0));
                }
            });
        }
        return dto;
    }

    public static <DTO extends BaseEntityActionDto> DTO resetInsertHandle(EntityMeta entityMeta, DTO parentDto, BiConsumer<DTO, DTO> biConsumer) {
        if (Objects.isNull(parentDto)) {
            return null;
        }
        if (Objects.nonNull(biConsumer)) {
            biConsumer.accept(parentDto, null);
        }
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            entityMeta.getChildren().stream().forEach(meta -> {
                Object dtoList = ReflectFieldUtil.getFieldValue((Object)parentDto, (String)meta.getDtoListName());
                if (Objects.nonNull(dtoList)) {
                    ArrayList dtoColl = Lists.newArrayList();
                    if (dtoList instanceof Collection) {
                        dtoColl.addAll((Collection)CastUtils.cast((Object)dtoList));
                    } else {
                        dtoColl.add(CastUtils.cast((Object)dtoList));
                    }
                    dtoColl.stream().forEach(subDto -> {
                        if (Objects.nonNull(biConsumer)) {
                            biConsumer.accept(parentDto, subDto);
                        }
                        DtoConvertUtil.resetInsertHandle(meta, subDto, biConsumer);
                    });
                }
            });
        }
        return parentDto;
    }

    public static <DTO extends BaseEntityActionDto> DTO forEach(EntityMeta entityMeta, DTO parentDto, Consumer<DTO> consumer) {
        if (Objects.isNull(parentDto)) {
            return null;
        }
        if (Objects.nonNull(consumer)) {
            consumer.accept(parentDto);
        }
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            entityMeta.getChildren().forEach(meta -> {
                Object dtoList = ReflectFieldUtil.getFieldValue((Object)parentDto, (String)meta.getDtoListName());
                if (Objects.nonNull(dtoList)) {
                    ArrayList dtoColl = Lists.newArrayList();
                    if (dtoList instanceof Collection) {
                        dtoColl.addAll((Collection)CastUtils.cast((Object)dtoList));
                    } else {
                        dtoColl.add(CastUtils.cast((Object)dtoList));
                    }
                    dtoColl.forEach(subDto -> DtoConvertUtil.forEach(meta, subDto, consumer));
                }
            });
        }
        return parentDto;
    }

    public static <DTO extends BaseEntityActionDto> void forEach(EntityMeta entityMeta, List<DTO> list, BiConsumer<EntityMeta, List<DTO>> biConsumer) {
        if (CollectionUtils.isEmpty(list)) {
            return;
        }
        if (Objects.nonNull(biConsumer)) {
            biConsumer.accept(entityMeta, list);
        }
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
            list.stream().forEach(dto -> entityMeta.getChildren().stream().forEach(meta -> {
                Object dtoList = ReflectFieldUtil.getFieldValue((Object)dto, (String)meta.getDtoListName());
                if (Objects.nonNull(dtoList)) {
                    ArrayList dtoColl = Lists.newArrayList();
                    if (dtoList instanceof Collection) {
                        dtoColl.addAll((Collection)CastUtils.cast((Object)dtoList));
                    } else {
                        dtoColl.add(CastUtils.cast((Object)dtoList));
                    }
                    if (Objects.nonNull(biConsumer)) {
                        biConsumer.accept((EntityMeta)meta, dtoColl);
                    }
                    DtoConvertUtil.forEach(meta, dtoColl, biConsumer);
                }
            }));
        }
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> defaultUpdateListToMap(EntityMeta entityMeta, List<DTO> list) {
        Consumer<BaseEntityActionDto> consumer = DtoFieldHelper::throwActionTypeIfAbsent;
        BiConsumer<BaseEntityActionDto, List> biConsumer = DtoFieldHelper::setParentIdIfAbsent;
        Map<Long, BaseEntityActionDto> newMap = DtoConvertUtil.listToMap(entityMeta, list, consumer, biConsumer, null);
        DtoConvertUtil.fixActionTypeByDFS(entityMeta, list);
        return newMap;
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> listToMap(EntityMeta entityMeta, List<DTO> list) {
        return DtoConvertUtil.listToMap(entityMeta, list, null, null, null);
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> listToMap(EntityMeta entityMeta, List<DTO> list, Predicate<DTO> filter) {
        return DtoConvertUtil.listToMap(entityMeta, list, null, null, filter);
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> listToMap(EntityMeta entityMeta, List<DTO> list, Consumer<DTO> consumer) {
        return DtoConvertUtil.listToMap(entityMeta, list, consumer, null, null);
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> listToMap(EntityMeta entityMeta, List<DTO> list, Consumer<DTO> consumer, Predicate<DTO> filter) {
        return DtoConvertUtil.listToMap(entityMeta, list, consumer, null, filter);
    }

    public static <DTO extends BaseEntityActionDto> Map<Long, DTO> listToMap(EntityMeta entityMeta, List<DTO> list, Consumer<DTO> consumer, BiConsumer<DTO, List<DTO>> biConsumer, Predicate<DTO> filter) {
        if (CollectionUtils.isEmpty(list)) {
            return Collections.emptyMap();
        }
        LinkedHashMap dataMap = Maps.newLinkedHashMapWithExpectedSize((int)list.size());
        list.stream().filter(dto -> {
            if (Objects.nonNull(filter)) {
                return Objects.nonNull(dto) && filter.test(dto);
            }
            return Objects.nonNull(dto);
        }).forEach(dto -> {
            if (Objects.nonNull(consumer)) {
                consumer.accept(dto);
            }
            dataMap.put(dto.getId(), dto);
            if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
                entityMeta.getChildren().stream().forEach(meta -> {
                    Object dtoList = ReflectFieldUtil.getFieldValue((Object)dto, (String)meta.getDtoListName());
                    if (Objects.nonNull(dtoList)) {
                        ArrayList dtoColl = Lists.newArrayList();
                        if (dtoList instanceof Collection) {
                            dtoColl.addAll((Collection)dtoList);
                        } else {
                            dtoColl.add((BaseEntityActionDto)dtoList);
                        }
                        if (Objects.nonNull(biConsumer)) {
                            biConsumer.accept(dto, dtoColl);
                        }
                        Map listToMap = DtoConvertUtil.listToMap(meta, dtoColl, consumer, biConsumer, filter);
                        Sets.SetView intersectionIds = Sets.intersection(dataMap.keySet(), listToMap.keySet());
                        if (CollectionUtils.isNotEmpty((Collection)intersectionIds)) {
                            throw new BusinessException().addError("聚合根内id冲突:" + intersectionIds);
                        }
                        dataMap.putAll(listToMap);
                    }
                });
            }
        });
        return dataMap;
    }

    public static <DTO extends BaseEntityActionDto> List<DTO> mergeMapData(EntityMeta entityMeta, Map<Long, DTO> dbMap, Map<Long, DTO> newMap) {
        if (MapUtils.isEmpty(dbMap) || MapUtils.isEmpty(newMap)) {
            return Collections.emptyList();
        }
        Map subDtoListNameMap = EntityMetaUtil.toSubDtoListNameMap((EntityMeta)entityMeta);
        dbMap.forEach((key, dbValue) -> {
            if (Objects.isNull(dbValue.getActionType())) {
                dbValue.setActionType(ActionType.NORMAL);
            }
            newMap.merge((Long)key, (Object)CastUtils.cast((Object)dbValue), (newValue, oldValue) -> {
                if (ActionType.UPDATE == newValue.getActionType()) {
                    Asserts.notNull((Object)newValue.getId(), (String)"actionType为UPDATE的id");
                    Set<String> enableNullFiledNamesSet = DtoConvertUtil.checkNullFieldsAndCollectNullFieldsNames(newValue);
                    List defaultIgnorePropertis = (List)subDtoListNameMap.get(newValue.getClass());
                    if (CollectionUtils.isNotEmpty((Collection)defaultIgnorePropertis)) {
                        CollectionUtils.addAll(enableNullFiledNamesSet, (Iterable)defaultIgnorePropertis);
                    }
                    List updatedFields = newValue.get__updatedFields();
                    DtoConvertUtil.copyValueIfTargetFieldIsNull(dbValue, newValue, Lists.newArrayList(enableNullFiledNamesSet), updatedFields);
                } else if (ActionType.NORMAL == newValue.getActionType()) {
                    return oldValue;
                }
                newValue.set__updatedFields(Collections.EMPTY_LIST);
                return newValue;
            });
        });
        List<Object> newDtoList = newMap.values().stream().filter(dto -> entityMeta.getDtoClass().equals(dto.getClass())).collect(Collectors.toList());
        Predicate<BaseEntityActionDto> filter = d -> ActionType.NORMAL != d.getActionType();
        newDtoList = DtoConvertUtil.forEachMergedChildDto(entityMeta, newDtoList, newMap, filter);
        return newDtoList;
    }

    private static <DTO extends BaseEntityActionDto> Set<String> checkNullFieldsAndCollectNullFieldsNames(DTO newValue) {
        if (CollectionUtils.isNotEmpty((Collection)newValue.get__updatedFields())) {
            for (String fieldName : newValue.get__updatedFields()) {
                DtoConvertUtil.checkFieldEnableNullValue(newValue, fieldName);
            }
        }
        HashSet nullFieldsName = Sets.newHashSet();
        List emptyFields = newValue.get__emptyFields();
        if (CollectionUtils.isEmpty((Collection)emptyFields)) {
            return nullFieldsName;
        }
        for (String fieldName : emptyFields) {
            DtoConvertUtil.checkFieldEnableNullValue(newValue, fieldName);
            Object fieldValue = ReflectFieldUtil.getFieldValue(newValue, (String)fieldName);
            if (!Objects.isNull(fieldValue)) continue;
            nullFieldsName.add(fieldName);
        }
        return nullFieldsName;
    }

    private static <DTO extends BaseEntityActionDto> void checkFieldEnableNullValue(DTO newValue, String fieldName) {
        Field field = ReflectFieldUtil.getField(newValue, (String)fieldName);
        Object fieldValue = ReflectFieldUtil.getFieldValue(newValue, (String)fieldName);
        if (fieldValue == null) {
            String filedDataType = AnnotationUtils.getCustomAttributeValue((AnnotatedElement)field, DtoAttribute.class, (String)"dataType");
            if (!ENABLED_NULL_FIELD_TYPE.contains(filedDataType)) {
                throw BusinessException.message((String)String.format("字段: %s 类型为: %s , 不支持设置为空 !", fieldName, filedDataType));
            }
            if (CAN_NOT_SET_NULL_FIELDS.contains(fieldName)) {
                throw BusinessException.message((String)String.format("预制字段: %s , 不支持设置为空 !", fieldName));
            }
        }
    }

    public static <DTO extends BaseEntityActionDto> List<DTO> forEachMergedChildDto(EntityMeta entityMeta, List<DTO> list, Map<Long, DTO> newMergedMap, Predicate<DTO> filter) {
        return DtoConvertUtil.forEachMergedChildDto(entityMeta, list, newMergedMap, null, filter);
    }

    public static <DTO extends BaseEntityActionDto> List<DTO> forEachMergedChildDto(EntityMeta entityMeta, List<DTO> list, Map<Long, DTO> newMergedMap) {
        return DtoConvertUtil.forEachMergedChildDto(entityMeta, list, newMergedMap, null, null);
    }

    public static <DTO extends BaseEntityActionDto> List<DTO> forEachMergedChildDto(EntityMeta entityMeta, List<DTO> list, Map<Long, DTO> newMergedMap, Consumer<DTO> consumer, Predicate<DTO> filter) {
        if (CollectionUtils.isEmpty(list)) {
            return Collections.emptyList();
        }
        list.stream().filter(dto -> Objects.nonNull(dto) && Objects.nonNull(dto.getId())).forEach(dto -> {
            if (Objects.nonNull(consumer)) {
                consumer.accept(dto);
            }
            if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren())) {
                entityMeta.getChildren().stream().forEach(meta -> {
                    List normalDtoList;
                    Object dtoList = ReflectFieldUtil.getFieldValue((Object)dto, (String)meta.getDtoListName());
                    List<Object> dtoColl = Lists.newArrayList();
                    AtomicBoolean change = new AtomicBoolean(false);
                    if (Objects.nonNull(dtoList)) {
                        List filterDtoList;
                        if (dtoList instanceof Collection) {
                            dtoColl.addAll((Collection)dtoList);
                        } else {
                            dtoColl.add((BaseEntityActionDto)dtoList);
                        }
                        if (Objects.nonNull(filter) && (filterDtoList = dtoColl.stream().filter(filter).collect(Collectors.toList())).size() != dtoColl.size()) {
                            change.set(true);
                            dtoColl = filterDtoList;
                        }
                    }
                    if (MapUtils.isNotEmpty((Map)newMergedMap) && CollectionUtils.isNotEmpty(normalDtoList = newMergedMap.values().stream().filter(d -> {
                        Object parentIdObj = ReflectFieldUtil.getFieldValue((Object)d, (String)"parentId");
                        return Objects.nonNull(parentIdObj) && Objects.equals(parentIdObj, dto.getId()) && d.getClass().equals(meta.getDtoClass()) && ActionType.NORMAL == d.getActionType();
                    }).collect(Collectors.toList()))) {
                        dtoColl.addAll(normalDtoList);
                        change.set(true);
                    }
                    HashSet deleteIds = Sets.newHashSet();
                    dtoColl = dtoColl.stream().filter(d -> {
                        if (ActionType.DELETE == d.getActionType()) {
                            deleteIds.add(d.getId());
                            change.set(true);
                            return false;
                        }
                        return true;
                    }).sorted(Comparator.comparing(d -> ((BaseDetailDto)d).getOrderNo(), Comparator.nullsLast(Integer::compareTo))).collect(Collectors.toList());
                    if (change.get()) {
                        if (!deleteIds.isEmpty()) {
                            dtoColl.stream().findFirst().ifPresent(obj -> {
                                Map extendMap = Optional.ofNullable(obj.getExtendMap()).orElseGet(() -> Maps.newLinkedHashMap());
                                extendMap.put(ActionType.DELETE.name(), deleteIds);
                                obj.setExtendMap(extendMap);
                                log.info("extendMap,{}:{}", (Object)ActionType.DELETE.name(), (Object)deleteIds);
                            });
                        }
                        DtoFieldHelper.set1ToNDtoList((BaseEntityActionDto)dto, (EntityMeta)meta, (List)dtoColl);
                    }
                    DtoConvertUtil.forEachMergedChildDto(meta, dtoColl, newMergedMap, consumer, filter);
                });
            }
        });
        return list;
    }

    public static <DTO extends BaseEntityActionDto> void fillDeletedData(EntityMeta entityMeta, List<DTO> newDtoList, Map<Long, DTO> newMap) {
        if (CollectionUtils.isNotEmpty((Collection)entityMeta.getChildren()) && CollectionUtils.isNotEmpty(newDtoList)) {
            newDtoList.stream().forEach(parentDto -> entityMeta.getChildren().stream().forEach(meta -> {
                List deleteDtoList = newMap.values().stream().filter(d -> ActionType.DELETE == d.getActionType()).filter(d -> meta.getDtoClass().equals(d.getClass())).filter(d -> {
                    Object parentId = ReflectFieldUtil.getFieldValue((Object)d, (String)"parentId");
                    return Objects.equals(parentDto.getId(), parentId);
                }).collect(Collectors.toList());
                if (CollectionUtils.isNotEmpty(deleteDtoList)) {
                    Object dtoList = ReflectFieldUtil.getFieldValue((Object)parentDto, (String)meta.getDtoListName());
                    ArrayList dtoColl = Lists.newArrayList();
                    if (Objects.nonNull(dtoList)) {
                        if (dtoList instanceof Collection) {
                            dtoColl.addAll((Collection)dtoList);
                        } else {
                            dtoColl.add((BaseEntityActionDto)dtoList);
                        }
                    }
                    dtoColl.addAll(deleteDtoList);
                    DtoFieldHelper.set1ToNDtoList((BaseEntityActionDto)parentDto, (EntityMeta)meta, (List)dtoColl);
                    DtoConvertUtil.fillDeletedData(meta, dtoColl, newMap);
                }
            }));
        }
    }

    public static <DTO extends BaseEntityActionDto> Map<ActionType, List<DTO>> groupByAction(List<DTO> list) {
        if (CollectionUtils.isEmpty(list)) {
            return Collections.emptyMap();
        }
        Map<ActionType, List<DTO>> mapList = list.stream().filter(a -> Objects.nonNull(a.getActionType())).collect(Collectors.groupingBy(dto -> dto.getActionType()));
        return mapList;
    }

    public static <DTO extends BaseEntityActionDto> void copyValueIfTargetFieldIsNull(DTO srcObj, DTO targetObj, List<String> ignorePropeties, List<String> updatedFields) {
        Asserts.isTrue((boolean)srcObj.getClass().equals(targetObj.getClass()), (String)"not the same class");
        Field[] fields = ReflectUtil.getFields(targetObj.getClass());
        List<Field> needCopyFields = Arrays.stream(fields).map(field -> {
            if (field.getName().equals("version")) {
                return field;
            }
            if (CollectionUtils.isNotEmpty((Collection)updatedFields) && updatedFields.contains(field)) {
                return null;
            }
            if (CollectionUtils.isNotEmpty((Collection)ignorePropeties) ? Objects.isNull(ReflectFieldUtil.getFieldValue((Object)targetObj, (Field)field)) && ignorePropeties.stream().noneMatch(property -> field.getName().equals(property)) : Objects.isNull(ReflectFieldUtil.getFieldValue((Object)targetObj, (Field)field))) {
                return field;
            }
            return null;
        }).filter(Objects::nonNull).collect(Collectors.toList());
        log.debug("needCopyFields:{}", needCopyFields);
        needCopyFields.forEach(field -> {
            Object object = ReflectFieldUtil.getFieldValue((Object)srcObj, (Field)field);
            if ("version".equals(field.getName()) && Objects.isNull(object)) {
                Optional.ofNullable(object).ifPresent(o -> ReflectUtil.setFieldValue((Object)targetObj, (Field)field, (Object)0));
            } else {
                Optional.ofNullable(object).ifPresent(o -> ReflectUtil.setFieldValue((Object)targetObj, (Field)field, (Object)object));
            }
        });
    }

    public static <DTO extends BaseEntityActionDto> void forEach(EntityMeta entityMeta, Collection<DTO> list, Collection<DTO> oldList, BiConsumer<EntityMeta, Pair<Collection<DTO>, Collection<DTO>>> biConsumer) {
        if (CollectionUtils.isEmpty(list) || biConsumer == null) {
            return;
        }
        biConsumer.accept(entityMeta, Pair.of(list, oldList));
        HashMap oldIdMap = oldList == null ? new HashMap() : oldList.stream().collect(Collectors.toMap(BaseEntityActionDto::getId, Function.identity()));
        for (BaseEntityActionDto dto : list) {
            List children = entityMeta.getChildren();
            if (!CollectionUtils.isNotEmpty((Collection)children)) continue;
            for (EntityMeta meta : children) {
                List<BaseEntityActionDto> dtoColl = DtoConvertUtil.getChildDtoList(dto, meta);
                List<BaseEntityActionDto> oldDtoColl = null;
                if (ActionType.UPDATE.equals((Object)dto.getActionType())) {
                    oldDtoColl = DtoConvertUtil.getChildDtoList((BaseEntityActionDto)oldIdMap.get(dto.getId()), meta);
                }
                DtoConvertUtil.forEach(meta, dtoColl, oldDtoColl, biConsumer);
            }
        }
    }

    private static <DTO extends BaseEntityActionDto> List<DTO> getChildDtoList(DTO parentDto, EntityMeta childMeta) {
        Object dtoList = ReflectFieldUtil.getFieldValue(parentDto, (String)childMeta.getDtoListName());
        ArrayList dtoColl = Lists.newArrayList();
        if (Objects.nonNull(dtoList)) {
            if (dtoList instanceof Collection) {
                dtoColl.addAll((Collection)CastUtils.cast((Object)dtoList));
            } else {
                dtoColl.add(CastUtils.cast((Object)dtoList));
            }
        }
        return dtoColl;
    }

    private static <DTO extends BaseEntityActionDto> boolean fixActionTypeByDFS(EntityMeta entityMeta, Collection<DTO> dtoList) {
        List childrenEntityMeta = entityMeta.getChildren();
        if (CollectionUtils.isEmpty((Collection)childrenEntityMeta)) {
            return dtoList.stream().anyMatch(DtoConvertUtil::checkUpdateActionType);
        }
        ArrayList<DTO> copyDtoList = new ArrayList<DTO>(dtoList);
        boolean flag = false;
        for (EntityMeta child : childrenEntityMeta) {
            BaseEntityActionDto dto;
            Object value;
            String dtoListName = child.getDtoListName();
            Iterator iterator = copyDtoList.iterator();
            while (iterator.hasNext() && (value = ReflectFieldUtil.getFieldValue((Object)(dto = (BaseEntityActionDto)iterator.next()), (String)dtoListName)) instanceof Collection) {
                Collection childrenEntity = (Collection)CastUtils.cast((Object)value);
                boolean setting = DtoConvertUtil.fixActionTypeByDFS(child, childrenEntity);
                if (setting && (Objects.isNull(dto.getActionType()) || ActionType.NORMAL == dto.getActionType())) {
                    dto.setActionType(ActionType.UPDATE);
                    iterator.remove();
                }
                if (flag || !DtoConvertUtil.checkUpdateActionType(dto)) continue;
                flag = true;
            }
        }
        return flag;
    }

    private static <DTO extends BaseEntityActionDto> boolean checkUpdateActionType(DTO dto) {
        ActionType actionType = dto.getActionType();
        return ActionType.UPDATE.equals((Object)actionType) || ActionType.DELETE.equals((Object)actionType) || ActionType.INSERT.equals((Object)actionType);
    }

    private static /* synthetic */ void lambda$null$0(EntityMeta meta, Supplier t, BiConsumer callback, BaseEntityActionDto subDto) {
        DtoConvertUtil.setValueHandle(meta, subDto, t, callback);
    }
}
