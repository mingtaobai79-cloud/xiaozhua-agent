/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.loader.ModulesProxyClassLoader
 *  com.seeyon.boot.starter.cache.util.CacheUtils
 *  com.seeyon.boot.starter.cache.util.RedisUtils
 *  com.seeyon.boot.starter.eventbus.annotation.EventHandler
 *  com.seeyon.boot.starter.eventbus.annotation.EventSubscribe
 *  com.seeyon.boot.starter.eventbus.interfaces.GenericEvent
 *  com.seeyon.boot.starter.udcrt.domain.service.ApproveFeatureService
 *  com.seeyon.boot.starter.udcrt.util.AnnotationUtils
 *  com.seeyon.boot.starter.udcrt.util.BpmDataUtil
 *  com.seeyon.boot.starter.udcrt.util.UdcReflectUtil
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.api.udc.BpmUdcApiService
 *  com.seeyon.bpm.dto.BpmStopDto
 *  com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto
 *  com.seeyon.udc.common.event.AfterDeleteEvent
 *  com.seeyon.udc.common.event.BeforeUpdateEvent
 *  com.seeyon.udc.common.utils.Nullable
 *  com.seeyon.udc.common.utils.ResponseUtils
 *  org.apache.dubbo.config.annotation.DubboReference
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 */
package com.seeyon.boot.starter.udcrt.event.listener;

import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.loader.ModulesProxyClassLoader;
import com.seeyon.boot.starter.cache.util.CacheUtils;
import com.seeyon.boot.starter.cache.util.RedisUtils;
import com.seeyon.boot.starter.eventbus.annotation.EventHandler;
import com.seeyon.boot.starter.eventbus.annotation.EventSubscribe;
import com.seeyon.boot.starter.eventbus.interfaces.GenericEvent;
import com.seeyon.boot.starter.udcrt.domain.service.ApproveFeatureService;
import com.seeyon.boot.starter.udcrt.util.AnnotationUtils;
import com.seeyon.boot.starter.udcrt.util.BpmDataUtil;
import com.seeyon.boot.starter.udcrt.util.UdcReflectUtil;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.api.udc.BpmUdcApiService;
import com.seeyon.bpm.dto.BpmStopDto;
import com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto;
import com.seeyon.udc.common.event.AfterDeleteEvent;
import com.seeyon.udc.common.event.BeforeUpdateEvent;
import com.seeyon.udc.common.utils.Nullable;
import com.seeyon.udc.common.utils.ResponseUtils;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.apache.dubbo.config.annotation.DubboReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

@EventHandler
public class ApprovalStateChangeListener {
    private static final Logger log = LoggerFactory.getLogger(ApprovalStateChangeListener.class);
    @DubboReference
    private BpmUdcApiService bpmUdcApiService;
    @Autowired
    private ApproveFeatureService approveFeatureService;

    @EventSubscribe
    public void onBillUpdate(BeforeUpdateEvent<?> event) throws ClassNotFoundException {
        Object data = event.getInfo();
        Object oldData = event.getOldInfo();
        boolean bpmRelativeEntity = this.isBpmRelativeEntity(data, (GenericEvent)event);
        if (bpmRelativeEntity) {
            Map extraParamMap = (Map)Nullable.ofNullable((Object)UdcReflectUtil.getFieldValue((Object)data, (String)"extraParamMap")).orElseGet(() -> new HashMap());
            if (this.isActionFromBpm(extraParamMap)) {
                log.info("bpm\u6267\u884c\u7ec8\u6b62\uff0c\u4e8b\u4ef6\u76d1\u542c\u4e0d\u5728\u89e6\u53d1\u7ec8\u6b62");
                return;
            }
            String oldState = UdcReflectUtil.getEnumFiledName((Object)oldData, (String)"statusType");
            String newState = UdcReflectUtil.getEnumFiledName((Object)data, (String)"statusType");
            log.info("\u66f4\u65b0\u4e8b\u4ef6\u76d1\u542c \uff0coldState:\u3010{}\u3011 , newState:\u3010{}\u3011", oldData, (Object)newState);
            switch (oldState) {
                case "PENDING_REVIEW": {
                    switch (newState) {
                        case "TERMINATED": {
                            this.stopBpmProcess(data, oldData);
                        }
                    }
                }
            }
        }
    }

    private boolean isActionFromBpm(Map<String, Object> extraParamMap) {
        return "bpm".equals(extraParamMap.get("processActionSource"));
    }

    @EventSubscribe
    public void onBillDelete(AfterDeleteEvent<?> event) throws ClassNotFoundException {
        Object data = event.getInfo();
        if (this.isBpmRelativeEntity(data, (GenericEvent)event)) {
            Long caseId = (Long)Nullable.ofNullable((Object)UdcReflectUtil.getFieldValue((Object)data, (String)"caseId")).ofLong().orElse((Object)-1L);
            if (caseId == -1L || caseId == 0L) {
                log.info("\u6ca1\u6709caseId\uff0c\u4e0d\u5220\u9664\u6d41\u7a0b");
                return;
            }
            Long id = (Long)Nullable.ofNullable((Object)UdcReflectUtil.getFieldValue((Object)data, (String)"id")).ofLong().orElse((Object)-1L);
            SingleResponse response = this.bpmUdcApiService.deleteCaseByIdForUdc(SingleRequest.from((Object)caseId), SingleRequest.from((Object)Apps.getRequestContext().getUserId()));
            ResponseUtils.responseResolve((SingleResponse)response, (String)"bpmUdcApiService.deleteCaseByIdForUdc");
            log.info("\u5355\u636e-{}-\u5220\u9664\uff0c\u540c\u65f6\u5220\u9664\u6d41\u7a0b\u6570\u636e-{}", (Object)id, (Object)caseId);
        }
    }

    private void stopBpmProcess(Object data, Object oldData) {
        log.info("\u7ec8\u6b62\u5355\u636e\u6d41\u7a0b...");
        BpmStopDto bpmStopDto = new BpmStopDto();
        bpmStopDto.setCaseId((Long)UdcReflectUtil.getFieldValue((Object)data, (String)"caseId"));
        bpmStopDto.setCurrentUserId(Apps.getRequestContext().getUserId());
        bpmStopDto.setCurrentAccountId(Apps.getRequestContext().getLoginOrgId());
        bpmStopDto.setOpinion((String)Nullable.ofNullable((Object)UdcReflectUtil.getFieldValue((Object)data, (String)"terminateReason")).ofString().orElse((Object)""));
        BpmPrefixForUdcResponseDto bpmPrefixParams = this.approveFeatureService.getBpmPrefixParams(data);
        if (bpmPrefixParams == null) {
            log.warn("\u6ca1\u6709\u53ef\u7528\u6d41\u7a0b\u53c2\u6570\uff0c\u65e0\u6cd5\u7ec8\u6b62\u6d41\u7a0b, data: \u3010{}\u3011 ", data);
            return;
        }
        List paramPathNames = bpmPrefixParams.getParamPathNames();
        Map paramMap = UdcReflectUtil.bean2Map((Object)data);
        Map processParamMap = BpmDataUtil.filterMapData((Map)paramMap, (List)paramPathNames);
        bpmStopDto.setBindParameters(processParamMap);
        log.info("\u8c03\u7528bpm\u7ec8\u6b62\u6d41\u7a0b, \u53c2\u6570:\u3010{}\u3011", (Object)bpmStopDto);
        RedisUtils.set((String)CacheUtils.getCompleteCacheKey((String)"BPM:STOP:CACHE", (String)UdcReflectUtil.getFieldValue((Object)data, (String)"id").toString()), (Object)true, (long)10L);
        SingleResponse response = this.bpmUdcApiService.stopForUdc(SingleRequest.from((Object)bpmStopDto));
        if (!response.success()) {
            log.error("bpm\u6d41\u7a0b\u7ec8\u6b62\uff0cdubbo\u8c03\u7528\u5931\u8d25\uff0c \u53c2\u6570:\u3010{}\u3011, responseMsg:\u3010{}\u3011", (Object)bpmStopDto, (Object)response.getMessage());
            throw new BusinessException("BPM_PROCESS_0012");
        }
        String terminateStatusType = UdcReflectUtil.getEnumFiledName((Object)oldData, (String)"statusType");
        UdcReflectUtil.setEnumFiled((Object)data, (String)"terminateStatusType", (String)terminateStatusType);
        UdcReflectUtil.setFieldValue((Object)data, (String)"terminatorId", (Object)Apps.getRequestContext().getUserId());
        UdcReflectUtil.setFieldValue((Object)data, (String)"terminateTime", (Object)new Date());
    }

    private boolean isBpmRelativeEntity(Object data, GenericEvent event) throws ClassNotFoundException {
        Class genericClass = event.getGenericClass();
        DtoInfo dtoInfo = genericClass.getDeclaredAnnotation(DtoInfo.class);
        String entity = dtoInfo.entity();
        Class clazz = ModulesProxyClassLoader.getInstance().loadClass(entity);
        if (Objects.isNull(clazz)) {
            throw BusinessException.message((String)("\u67e5\u8be2\u4e0d\u5230\u5b9e\u4f53\uff1a" + entity + "\u5bf9\u5e94\u7684Class\u4fe1\u606f"));
        }
        String[] billStereotype = new String[]{"bill", "archive", "archiveTree", "form"};
        return AnnotationUtils.isEntityFrom((Class)clazz, (String[])billStereotype);
    }
}
