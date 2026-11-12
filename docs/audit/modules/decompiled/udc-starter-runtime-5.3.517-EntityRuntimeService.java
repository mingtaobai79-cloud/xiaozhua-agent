/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.bean.BeanUtil
 *  com.google.common.collect.Maps
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.EntityAttribute
 *  com.seeyon.boot.domain.entity.BaseEntity
 *  com.seeyon.boot.starter.customplan.domain.service.FormPermissionAuthService
 *  com.seeyon.boot.starter.customplan.dto.BpmFromPermissionCheckDto
 *  com.seeyon.boot.starter.lowcode.callback.PermissionCallBack
 *  com.seeyon.boot.starter.lowcode.core.EntityMeta
 *  com.seeyon.boot.starter.lowcode.util.EntityMetaUtil
 *  com.seeyon.boot.starter.udcrt.domain.service.UdcSerialConfigService
 *  com.seeyon.boot.starter.udcrt.util.UdcReflectUtil
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.boot.util.JsonUtils
 *  com.seeyon.bpm.dto.BpmFormPermissionContentDto
 *  com.seeyon.bpm.dto.BpmFormPermissionIncludeContentDto
 *  com.seeyon.bpm.enums.BpmDeviceTypeEnum
 *  com.seeyon.bpm.enums.BpmFormDesensitizedTypeEnum
 *  com.seeyon.bpm.enums.BpmFormPermissionCodeEnum
 *  com.seeyon.bpm.enums.BpmFormPermissionContentInitValueTriggerConditionEnum
 *  com.seeyon.bpm.enums.BpmFormPermissionContentTypeEnum
 *  com.seeyon.bpm.enums.BpmFormPermissionSourceTypeEnum
 *  com.seeyon.bpm.enums.BpmFormPermissionTypeEnum
 *  com.seeyon.udc.common.dto.BaseEntityActionDto
 *  com.seeyon.udc.common.dto.BaseRootDto
 *  org.apache.commons.collections.CollectionUtils
 *  org.apache.commons.collections.MapUtils
 *  org.apache.commons.lang3.StringUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.data.util.CastUtils
 *  org.springframework.stereotype.Service
 */
package com.seeyon.boot.starter.udcrt.domain.service;

import cn.hutool.core.bean.BeanUtil;
import com.google.common.collect.Maps;
import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.EntityAttribute;
import com.seeyon.boot.domain.entity.BaseEntity;
import com.seeyon.boot.starter.customplan.domain.service.FormPermissionAuthService;
import com.seeyon.boot.starter.customplan.dto.BpmFromPermissionCheckDto;
import com.seeyon.boot.starter.lowcode.callback.PermissionCallBack;
import com.seeyon.boot.starter.lowcode.core.EntityMeta;
import com.seeyon.boot.starter.lowcode.util.EntityMetaUtil;
import com.seeyon.boot.starter.udcrt.domain.service.UdcSerialConfigService;
import com.seeyon.boot.starter.udcrt.util.UdcReflectUtil;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.boot.util.JsonUtils;
import com.seeyon.bpm.dto.BpmFormPermissionContentDto;
import com.seeyon.bpm.dto.BpmFormPermissionIncludeContentDto;
import com.seeyon.bpm.enums.BpmDeviceTypeEnum;
import com.seeyon.bpm.enums.BpmFormDesensitizedTypeEnum;
import com.seeyon.bpm.enums.BpmFormPermissionCodeEnum;
import com.seeyon.bpm.enums.BpmFormPermissionContentInitValueTriggerConditionEnum;
import com.seeyon.bpm.enums.BpmFormPermissionContentTypeEnum;
import com.seeyon.bpm.enums.BpmFormPermissionSourceTypeEnum;
import com.seeyon.bpm.enums.BpmFormPermissionTypeEnum;
import com.seeyon.udc.common.dto.BaseEntityActionDto;
import com.seeyon.udc.common.dto.BaseRootDto;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.CastUtils;
import org.springframework.stereotype.Service;

@Service
public class EntityRuntimeService
implements PermissionCallBack {
    private static final Logger log = LoggerFactory.getLogger(EntityRuntimeService.class);
    private static final String CUSTOM_DATA_TYPE = "customDataType";
    private static final String GET = "get";
    private static final String FORM_PERMISSION_ID = "formPermissionId";
    private static final String FORM_PERMISSION_DATA = "formPermissionData";
    private static final String FORM_BPM_INFO = "bpmInfo";
    @Autowired
    private UdcSerialConfigService serialConfigService;
    @Autowired
    private FormPermissionAuthService formPermissionAuthService;

    public <T extends BaseEntityActionDto> T buildInitialValue(EntityMeta entityMeta, T oldData, T newData) {
        if (Objects.isNull(newData)) {
            return null;
        }
        if (newData instanceof BaseRootDto) {
            BaseRootDto rootDto = (BaseRootDto)newData;
            Map extraParamMap = rootDto.getExtraParamMap();
            if (MapUtils.isEmpty((Map)extraParamMap)) {
                return newData;
            }
            Object formPermissionId = extraParamMap.get(FORM_PERMISSION_ID);
            if (Objects.isNull(formPermissionId)) {
                return newData;
            }
            BpmFromPermissionCheckDto<T> planPermissionDto = this.getBpmFromPermissionCheckDto(entityMeta, oldData, newData, extraParamMap);
            rootDto.setExtraParamMap(null);
            BaseEntityActionDto result = (BaseEntityActionDto)this.formPermissionAuthService.buildInitialValue(planPermissionDto);
            rootDto.setExtraParamMap(extraParamMap);
            return (T)result;
        }
        return newData;
    }

    public <T extends BaseEntityActionDto> void requiredValidate(EntityMeta entityMeta, T oldData, T newData) {
        if (Objects.isNull(newData)) {
            return;
        }
        if (newData instanceof BaseRootDto) {
            BpmFormPermissionTypeEnum permissionType;
            BaseRootDto rootDto = (BaseRootDto)newData;
            if (!rootDto.isValidate()) {
                return;
            }
            Map extraParamMap = rootDto.getExtraParamMap();
            if (MapUtils.isEmpty((Map)extraParamMap)) {
                return;
            }
            Object formPermissionId = extraParamMap.get(FORM_PERMISSION_ID);
            if (Objects.isNull(formPermissionId)) {
                return;
            }
            BpmFromPermissionCheckDto<T> planPermissionDto = this.getBpmFromPermissionCheckDto(entityMeta, oldData, newData, extraParamMap);
            BpmFormPermissionTypeEnum bpmFormPermissionTypeEnum = permissionType = planPermissionDto.getPermissionDataDto() == null ? BpmFormPermissionTypeEnum.NONE : planPermissionDto.getPermissionDataDto().getPermissionType();
            if (BpmFormPermissionTypeEnum.READONLY == permissionType) {
                return;
            }
            rootDto.setExtraParamMap(null);
            Set nullFieldNames = this.formPermissionAuthService.requiredValidate(planPermissionDto);
            rootDto.setExtraParamMap(extraParamMap);
            if (CollectionUtils.isNotEmpty((Collection)nullFieldNames)) {
                String errorMsg = nullFieldNames.stream().collect(Collectors.joining(","));
                log.error("{}\u4e0d\u80fd\u4e3a\u7a7a", (Object)errorMsg);
            }
        }
    }

    private <T extends BaseEntityActionDto> BpmFromPermissionCheckDto<T> getBpmFromPermissionCheckDto(EntityMeta entityMeta, T oldData, T newData, Map<String, Object> extraParamMap) {
        Object formPermissionId = extraParamMap.get(FORM_PERMISSION_ID);
        Object formPermissionData = extraParamMap.get(FORM_PERMISSION_DATA);
        Map expressionExtParam = (Map)CastUtils.cast((Object)extraParamMap.get(FORM_BPM_INFO));
        BpmFromPermissionCheckDto planPermissionDto = new BpmFromPermissionCheckDto();
        planPermissionDto.setDataDto(newData);
        planPermissionDto.setOldDataDto(oldData);
        planPermissionDto.setSourceId(String.valueOf(formPermissionId));
        Optional.ofNullable(formPermissionData).ifPresent(data -> {
            if (data instanceof Map) {
                Map dataMap = (Map)data;
                BpmFormPermissionIncludeContentDto dto = this.mapToBpmFormPermissionIncludeContentDto(dataMap);
                planPermissionDto.setPermissionDataDto(dto);
            } else {
                planPermissionDto.setPermissionDataDto((BpmFormPermissionIncludeContentDto)BeanUtil.toBean((Object)data, BpmFormPermissionIncludeContentDto.class));
            }
            Optional.ofNullable(planPermissionDto.getPermissionDataDto()).ifPresent(item -> {
                if (CollectionUtils.isNotEmpty((Collection)item.getContentDtos())) {
                    ArrayList<String> entityFullNames = new ArrayList<String>();
                    entityFullNames.add(entityMeta.getFullName());
                    Consumer<EntityMeta> getFullNameConsumer = meta -> {
                        if (Objects.nonNull(meta)) {
                            entityFullNames.add(meta.getFullName());
                        }
                    };
                    EntityMetaUtil.forEachMeta((EntityMeta)entityMeta, getFullNameConsumer);
                    List filteredContentDtos = item.getContentDtos().stream().filter(dto -> Objects.equals(BpmFormPermissionContentTypeEnum.FIELD, dto.getType())).filter(dto -> entityFullNames.contains(StringUtils.substringBeforeLast((String)dto.getFieldName(), (String)"."))).collect(Collectors.toList());
                    item.setContentDtos(filteredContentDtos);
                }
            });
        });
        planPermissionDto.setExpressionExtParam(expressionExtParam);
        return planPermissionDto;
    }

    public void setEntityValue(BaseDto dto, Class<? extends BaseEntity> entityClass) {
        List<Field> serialFields = this.getSerialField(entityClass);
        this.setSerialValue(dto, entityClass, serialFields);
    }

    private void setSerialValue(BaseDto dto, Class<? extends BaseEntity> entityClass, List<Field> serialFields) {
        if (CollectionUtils.isNotEmpty(serialFields)) {
            HashMap values = Maps.newHashMapWithExpectedSize((int)serialFields.size());
            for (Field field : serialFields) {
                log.info("Begin to generate serial number: [{}.{}]", (Object)entityClass.getCanonicalName(), (Object)field.getName());
                Object value = UdcReflectUtil.getFieldValue((Object)dto, (String)field.getName());
                if (Objects.isNull(value) || StringUtils.isBlank((CharSequence)value.toString())) {
                    String entityFullName = entityClass.getCanonicalName();
                    String fieldFullName = entityFullName + "." + field.getName();
                    String serialNumber = this.serialConfigService.genSerialNumberBySourceFullName((Object)dto, fieldFullName);
                    values.put(field.getName(), serialNumber);
                    continue;
                }
                log.info("Field [{}] has value [{}], don't generate serial number", (Object)field.getName(), value);
            }
            if (MapUtils.isNotEmpty((Map)values)) {
                if (log.isInfoEnabled()) {
                    log.info("\u51c6\u5907\u7ed9\u6570\u636e\u56de\u586b\u503c: [{}]", (Object)JsonUtils.toJson((Object)values));
                }
                BeanUtil.fillBeanWithMap((Map)values, (Object)dto, (boolean)false);
            }
        }
    }

    public void setEntityValue(List<? extends BaseDto> dtos, Class<? extends BaseEntity> entityClass) {
        if (CollectionUtils.isEmpty(dtos)) {
            return;
        }
        List<Field> serialFields = this.getSerialField(entityClass);
        dtos.forEach(dto -> this.setSerialValue((BaseDto)dto, entityClass, serialFields));
    }

    public List<Field> getSerialField(Class<? extends BaseEntity> entityClass) {
        List filedList = UdcReflectUtil.getFiledList(entityClass);
        if (CollectionUtils.isEmpty((Collection)filedList)) {
            log.info("the field length is zero, while set value.");
            return null;
        }
        ArrayList<Field> serialFields = new ArrayList<Field>();
        for (Field field : filedList) {
            Custom[] customs;
            EntityAttribute entityAttribute = field.getAnnotation(EntityAttribute.class);
            if (!Objects.nonNull(entityAttribute)) continue;
            for (Custom custom : customs = entityAttribute.customs()) {
                CustomAttribute[] properties;
                String customName = custom.name();
                if (!CUSTOM_DATA_TYPE.equals(customName)) continue;
                for (CustomAttribute customAttribute : properties = custom.properties()) {
                    String attributeName = customAttribute.name();
                    String attributeValue = customAttribute.value();
                    if (!"name".equals(attributeName) || !"Serial".equals(attributeValue)) continue;
                    serialFields.add(field);
                }
            }
        }
        return serialFields;
    }

    private BpmFormPermissionIncludeContentDto mapToBpmFormPermissionIncludeContentDto(Map<String, Object> dataMap) {
        if (dataMap == null) {
            return null;
        }
        BpmFormPermissionIncludeContentDto dto = new BpmFormPermissionIncludeContentDto();
        dataMap.forEach((key, value) -> {
            if ("id".equals(key) && value != null && value instanceof Long) {
                dto.setId((Long)value);
            }
            if ("validate".equals(key) && value != null && value instanceof Boolean) {
                dto.setValidate(((Boolean)value).booleanValue());
            }
            if ("caption".equals(key) && value != null && value instanceof String) {
                dto.setCaption((String)value);
            }
            if ("templateId".equals(key) && value != null && value instanceof Long) {
                dto.setTemplateId((Long)value);
            }
            if ("pageUrl".equals(key) && value != null && value instanceof String) {
                dto.setPageUrl((String)value);
            }
            if ("pageGroupId".equals(key) && value != null && (value instanceof Integer || value instanceof Long)) {
                dto.setPageGroupId(Long.valueOf(Long.parseLong(value.toString())));
            }
            if ("sourceType".equals(key) && value != null && value instanceof String) {
                dto.setSourceType(BpmFormPermissionSourceTypeEnum.valueOf((String)((String)value)));
            }
            if ("permissionsCode".equals(key) && value != null && value instanceof String) {
                dto.setPermissionsCode(BpmFormPermissionCodeEnum.valueOf((String)((String)value)));
            }
            if ("mobilePageUrl".equals(key) && value != null && value instanceof String) {
                dto.setMobilePageUrl((String)value);
            }
            if ("pageParameter".equals(key) && value != null && value instanceof String) {
                dto.setPageParameter((String)value);
            }
            if ("mobilePageParameter".equals(key) && value != null && value instanceof String) {
                dto.setMobilePageParameter((String)value);
            }
            if ("pcSubPage".equals(key) && value != null && value instanceof String) {
                dto.setPcSubPage((String)value);
            }
            if ("mobileSubPage".equals(key) && value != null && value instanceof String) {
                dto.setMobileSubPage((String)value);
            }
            if ("contentDtos".equals(key) && value != null && value instanceof List) {
                ArrayList<BpmFormPermissionContentDto> bpmFormPermissionContentDtos = new ArrayList<BpmFormPermissionContentDto>();
                List list = (List)value;
                for (Object obj : list) {
                    BpmFormPermissionContentDto bpmFormPermissionContentDto;
                    if (obj == null || !(obj instanceof Map) || (bpmFormPermissionContentDto = this.mapToBpmFormPermissionContentDto((Map)obj)) == null) continue;
                    bpmFormPermissionContentDtos.add(bpmFormPermissionContentDto);
                }
                dto.setContentDtos(bpmFormPermissionContentDtos);
            }
            if ("permissionType".equals(key)) {
                if (value != null && value instanceof BpmFormPermissionTypeEnum) {
                    dto.setPermissionType((BpmFormPermissionTypeEnum)value);
                } else if (value != null && value instanceof String && StringUtils.isNotEmpty((CharSequence)((String)value))) {
                    dto.setPermissionType(BpmFormPermissionTypeEnum.valueOf((String)((String)value)));
                }
            }
        });
        return dto;
    }

    private BpmFormPermissionContentDto mapToBpmFormPermissionContentDto(Map<String, Object> map) {
        if (map == null) {
            return null;
        }
        BpmFormPermissionContentDto dto = new BpmFormPermissionContentDto();
        map.forEach((key, value) -> {
            if ("validate".equals(key) && value != null && value instanceof Boolean) {
                dto.setValidate(((Boolean)value).booleanValue());
            }
            if ("id".equals(key) && value != null && value instanceof Long) {
                dto.setId((Long)value);
            }
            if ("guid".equals(key) && value != null && value instanceof Long) {
                dto.setGuid((Long)value);
            }
            if ("permissionId".equals(key) && value != null && value instanceof Long) {
                dto.setPermissionId((Long)value);
            }
            if ("widgetId".equals(key) && value != null && value instanceof String) {
                dto.setWidgetId((String)value);
            }
            if ("fieldId".equals(key) && value != null && (value instanceof Long || value instanceof Integer)) {
                dto.setFieldId(Long.valueOf(Long.parseLong(value.toString())));
            }
            if ("fieldName".equals(key) && value != null && value instanceof String) {
                dto.setFieldName((String)value);
            }
            if ("type".equals(key) && value != null && value instanceof String) {
                dto.setType(BpmFormPermissionContentTypeEnum.valueOf((String)((String)value)));
            }
            if ("widgetDeviceType".equals(key) && value != null && value instanceof String) {
                dto.setWidgetDeviceType(BpmDeviceTypeEnum.valueOf((String)((String)value)));
            }
            if ("content".equals(key) && value != null && value instanceof String) {
                dto.setContent((String)value);
            }
            if ("fieldPath".equals(key) && value != null && value instanceof String) {
                dto.setFieldPath((String)value);
            }
            if ("pageAuth".equals(key) && value != null && value instanceof Boolean) {
                dto.setPageAuth((Boolean)value);
            }
            if ("required".equals(key) && value != null && value instanceof Boolean) {
                dto.setRequired((Boolean)value);
            }
            if ("requiredExpr".equals(key) && value != null && value instanceof String) {
                dto.setRequiredExpr((String)value);
            }
            if ("widgetStatus".equals(key) && value != null && value instanceof String) {
                dto.setWidgetStatus((String)value);
            }
            if ("widgetStatusExpr".equals(key) && value != null && value instanceof String) {
                dto.setWidgetStatusExpr((String)value);
            }
            if ("initValue".equals(key) && value != null && value instanceof String) {
                dto.setInitValue((String)value);
            }
            if ("initValueExpr".equals(key) && value != null && value instanceof String) {
                dto.setInitValueExpr((String)value);
            }
            if ("title".equals(key) && value != null && value instanceof String) {
                dto.setTitle((String)value);
            }
            if ("desensitized".equals(key) && value != null && value instanceof String) {
                dto.setDesensitized(BpmFormDesensitizedTypeEnum.valueOf((String)((String)value)));
            }
            if ("initValueTriggerConditionEnum".equals(key) && value != null && value instanceof String) {
                dto.setInitValueTriggerConditionEnum(BpmFormPermissionContentInitValueTriggerConditionEnum.valueOf((String)((String)value)));
            }
        });
        return dto;
    }
}
