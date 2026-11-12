/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.alibaba.nacos.shaded.com.google.common.collect.Lists
 *  com.seeyon.boot.starter.extmetadata.dto.UdcAppServiceMetaDataDto
 *  com.seeyon.boot.starter.extmetadata.enums.EntityActionEnum
 *  org.apache.commons.collections.CollectionUtils
 */
package com.seeyon.boot.starter.extmetadata.utils;

import com.alibaba.nacos.shaded.com.google.common.collect.Lists;
import com.seeyon.boot.starter.extmetadata.dto.UdcAppServiceMetaDataDto;
import com.seeyon.boot.starter.extmetadata.enums.EntityActionEnum;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import org.apache.commons.collections.CollectionUtils;

public class UdcMethod2ActionUtil {
    public static Map<String, List<String>> method2ActionMap = new HashMap<String, List<String>>();

    public static List<EntityActionEnum> getActionEnumByAppServiceMetadata(UdcAppServiceMetaDataDto appServiceMetadataDto) {
        ArrayList<EntityActionEnum> actionEnumList = new ArrayList<EntityActionEnum>();
        if (Objects.isNull(appServiceMetadataDto) || CollectionUtils.isEmpty((Collection)appServiceMetadataDto.getMethods())) {
            return actionEnumList;
        }
        return appServiceMetadataDto.getMethods().stream().filter(item -> method2ActionMap.containsKey(item.getMethodName())).flatMap(item -> method2ActionMap.get(item.getMethodName()).stream()).distinct().map(EntityActionEnum::valueOf).collect(Collectors.toList());
    }

    static {
        method2ActionMap.put("runtimeCopy", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_COPY_DATA.name()}));
        method2ActionMap.put("exportExcel", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_EXPORT.name()}));
        method2ActionMap.put("getCascadeDefaultValue", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_COPY_DATA.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name(), EntityActionEnum.ENTITY_SUBMIT.name(), EntityActionEnum.ENTITY_WITHDRAW.name(), EntityActionEnum.ENTITY_DATA_LOG.name(), EntityActionEnum.formconvert.name(), EntityActionEnum.downloadAll.name(), EntityActionEnum.labelPrint.name(), EntityActionEnum.attention.name(), EntityActionEnum.sensitiveWords.name()}));
        method2ActionMap.put("selectCascadeByConditions", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SELECT_SINGLE.name()}));
        method2ActionMap.put("dynamicJoinSelect", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SELECT_LIST.name()}));
        method2ActionMap.put("importExcel", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_IMPORT.name()}));
        method2ActionMap.put("create", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name()}));
        method2ActionMap.put("createBatch", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name()}));
        method2ActionMap.put("create4Bpm", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SUBMIT.name()}));
        method2ActionMap.put("update", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name()}));
        method2ActionMap.put("updateBatch", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name()}));
        method2ActionMap.put("update4Bpm", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SUBMIT.name()}));
        method2ActionMap.put("operateRootBatch", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_SAVE_NEW.name(), EntityActionEnum.ENTITY_SAVE_COPY.name(), EntityActionEnum.ENTITY_SAVE.name(), EntityActionEnum.ENTITY_SAVE_DRAFT.name()}));
        method2ActionMap.put("deleteById", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_DELETE.name()}));
        method2ActionMap.put("deleteByIds", Lists.newArrayList((Object[])new String[]{EntityActionEnum.ENTITY_DELETE.name()}));
    }
}
