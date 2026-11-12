/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.map.MapUtil
 *  com.google.common.collect.Maps
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.context.RequestContext
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.lowcode.callback.ApprovalCallBack
 *  com.seeyon.boot.starter.lowcode.dto.ApprovalContext
 *  com.seeyon.boot.starter.udcrt.domain.service.BpmRetryService
 *  com.seeyon.boot.starter.udcrt.domain.service.UdcSerialConfigService
 *  com.seeyon.boot.starter.udcrt.dto.BpmProcessLaunchResultDto
 *  com.seeyon.boot.starter.udcrt.util.BpmDataUtil
 *  com.seeyon.boot.starter.udcrt.util.UdcReflectUtil
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.util.StringUtils
 *  com.seeyon.bpm.api.udc.BpmUdcApiService
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.dto.BpmOperationNodeDto
 *  com.seeyon.bpm.dto.BpmPrefixForUdcDto
 *  com.seeyon.bpm.dto.ChangeNodeRequestDto
 *  com.seeyon.bpm.dto.PreMatchRequestDto
 *  com.seeyon.bpm.dto.approval.BpmApiSendApiResponseDto
 *  com.seeyon.bpm.dto.approval.BpmOperationRepealUdcDto
 *  com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto
 *  com.seeyon.bpm.dto.approval.BpmSaveDraftUdcDto
 *  com.seeyon.bpm.dto.approval.BpmSaveDraftUdcResponseDto
 *  com.seeyon.bpm.dto.approval.BpmSendUdcDto
 *  com.seeyon.bpm.enums.CaseTypeEnum
 *  com.seeyon.bpm.enums.PageTypeEnum
 *  com.seeyon.udc.common.constant.UdcCommonConstant
 *  com.seeyon.udc.common.dto.BaseRootDto
 *  com.seeyon.udc.common.utils.Nullable
 *  com.seeyon.udc.common.utils.UdcJsonUtils
 *  org.apache.commons.collections.CollectionUtils
 *  org.apache.commons.collections.MapUtils
 *  org.apache.dubbo.config.annotation.DubboReference
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.data.util.CastUtils
 *  org.springframework.stereotype.Service
 */
package com.seeyon.boot.starter.udcrt.domain.service;

import cn.hutool.core.map.MapUtil;
import com.google.common.collect.Maps;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.context.RequestContext;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.lowcode.callback.ApprovalCallBack;
import com.seeyon.boot.starter.lowcode.dto.ApprovalContext;
import com.seeyon.boot.starter.udcrt.domain.service.BpmRetryService;
import com.seeyon.boot.starter.udcrt.domain.service.UdcSerialConfigService;
import com.seeyon.boot.starter.udcrt.dto.BpmProcessLaunchResultDto;
import com.seeyon.boot.starter.udcrt.util.BpmDataUtil;
import com.seeyon.boot.starter.udcrt.util.UdcReflectUtil;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.bpm.api.udc.BpmUdcApiService;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.dto.BpmOperationNodeDto;
import com.seeyon.bpm.dto.BpmPrefixForUdcDto;
import com.seeyon.bpm.dto.ChangeNodeRequestDto;
import com.seeyon.bpm.dto.PreMatchRequestDto;
import com.seeyon.bpm.dto.approval.BpmApiSendApiResponseDto;
import com.seeyon.bpm.dto.approval.BpmOperationRepealUdcDto;
import com.seeyon.bpm.dto.approval.BpmPrefixForUdcResponseDto;
import com.seeyon.bpm.dto.approval.BpmSaveDraftUdcDto;
import com.seeyon.bpm.dto.approval.BpmSaveDraftUdcResponseDto;
import com.seeyon.bpm.dto.approval.BpmSendUdcDto;
import com.seeyon.bpm.enums.CaseTypeEnum;
import com.seeyon.bpm.enums.PageTypeEnum;
import com.seeyon.udc.common.constant.UdcCommonConstant;
import com.seeyon.udc.common.dto.BaseRootDto;
import com.seeyon.udc.common.utils.Nullable;
import com.seeyon.udc.common.utils.UdcJsonUtils;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.MapUtils;
import org.apache.dubbo.config.annotation.DubboReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.CastUtils;
import org.springframework.stereotype.Service;

@Service
public class ApproveFeatureService
implements ApprovalCallBack {
    private static final Logger log = LoggerFactory.getLogger(ApproveFeatureService.class);
    @Autowired
    private UdcSerialConfigService serialConfigService;
    @DubboReference
    private BpmUdcApiService bpmUdcApiService;
    @Autowired
    private BpmRetryService bpmRetryService;
    private static final String BPM_COMMENT = "bpmComment";
    private static final String PRE_MATCH_REQUEST_DTO = "preMatchRequestDto";
    private static final String ATTACHMENT_STORAGEIDS = "attachmentStorageIds";
    private static final String BPM_COMMENT_ATTACHMENT_TEMPLATE = "{id=%s, fileName=%s, size=%s , storageKey=%s}";
    private static final String BPM_COMMENT_ATTACHMENT_ATTR_TEMPLATE = "%s=%s";
    private static final String BPM_PREFIX_PARAM_KEY = "bpmPrefixForUdcResponseDto";

    public void beforeApprovalCreate(ApprovalContext context) {
        BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto = this.getBpmPrefixParams(context.getProcessData());
        context.addParamter("bpmPrefix", (Object)bpmPrefixForUdcResponseDto);
    }

    public void afterApprovalCreate(ApprovalContext context) {
        String targetStatusType = context.getTargetStatusType();
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = this.startProcess0(context.getProcessData(), targetStatusType, null, (BpmPrefixForUdcResponseDto)CastUtils.cast((Object)context.getParamter("bpmPrefix")));
        context.addParamter("bpm", (Object)bpmProcessLaunchResultDto);
        Optional.ofNullable(bpmProcessLaunchResultDto).ifPresent(dto -> context.addErrorMsg((Object)dto.getErrorMsg()));
        context.addParamter("bpmProcessType", (Object)this.isMainProcess(bpmProcessLaunchResultDto));
    }

    public void beforeApprovalUpdate(ApprovalContext context) {
        BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto = this.getBpmPrefixParams(context.getProcessData());
        context.addParamter("bpmPrefix", (Object)bpmPrefixForUdcResponseDto);
    }

    public void afterApprovalUpdate(ApprovalContext context) {
        String oldStatus = ((Enum)context.getProcessData().getExtendMap().get("oldStatusType")).name();
        String targetStatus = context.getTargetStatusType();
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = this.startProcess0(context.getProcessData(), targetStatus, oldStatus, (BpmPrefixForUdcResponseDto)CastUtils.cast((Object)context.getParamter("bpmPrefix")));
        context.addParamter("bpm", (Object)bpmProcessLaunchResultDto);
        Optional.ofNullable(bpmProcessLaunchResultDto).ifPresent(dto -> context.addErrorMsg((Object)dto.getErrorMsg()));
        context.addParamter("bpmProcessType", (Object)this.isMainProcess(bpmProcessLaunchResultDto));
    }

    public void beforeApprovalCreateValidate(ApprovalContext context) {
    }

    public void beforeApprovalUpdateValidate(ApprovalContext context) {
    }

    public BpmPrefixForUdcResponseDto getBpmPrefixParams(Object data) {
        String entityFullName = this.getEntityFullName(data);
        BpmPrefixForUdcDto param = new BpmPrefixForUdcDto();
        param.setRootEntityName(entityFullName);
        try {
            Map extraParamMap;
            Long templateId = (Long)UdcReflectUtil.getFieldValue((Object)data, (String)"templateId");
            param.setTemplateId(templateId);
            if (data instanceof BaseRootDto && MapUtils.isNotEmpty((Map)(extraParamMap = ((BaseRootDto)data).getExtraParamMap()))) {
                param.setPageGuid((Long)Nullable.ofNullable(extraParamMap.get("pageGuid")).ofLong().get());
                param.setTemplateGuid((Long)Nullable.ofNullable(extraParamMap.get("templateGuid")).ofLong().get());
                param.setPageUrl((String)Nullable.ofNullable(extraParamMap.get("pageUrl")).ofString().orElse((Object)""));
                param.setPageParameter((String)Nullable.ofNullable(extraParamMap.get("pageParameter")).ofString().orElse((Object)""));
                String pageType = (String)Nullable.ofNullable(extraParamMap.get("pageType")).ofString().orElse((Object)"");
                param.setCaseId((Long)UdcReflectUtil.getFieldValue((Object)data, (String)"caseId"));
                PageTypeEnum[] values = PageTypeEnum.values();
                boolean illegal = true;
                for (PageTypeEnum pageTypeEnum : values) {
                    if (!pageTypeEnum.name().equals(pageType)) continue;
                    illegal = false;
                }
                if (illegal) {
                    pageType = null;
                }
                param.setPageType(pageType == null ? null : PageTypeEnum.valueOf((String)pageType));
            }
        }
        catch (Exception e) {
            log.error("\u83b7\u53d6\u9884\u53d1\u9001\u8bf7\u6c42\u53c2\u6570\u5931\u8d25, data:\u3010{}\u3011", data, (Object)e);
            throw new BusinessException("BPM_PROCESS_0007");
        }
        SingleResponse callResponse = this.bpmUdcApiService.prefixForUdc(SingleRequest.from((Object)param));
        if (!callResponse.success()) {
            if (callResponse.getCode().equals("BOOT_1004")) {
                throw new BusinessException("BOOT_1004");
            }
            log.error("\u83b7\u53d6bpm\u6d41\u7a0b\u53c2\u6570\u5931\u8d25, data:\u3010{}\u3011, message:\u3010{}\u3011", data, (Object)callResponse.getMessage());
            throw new BusinessException("BPM_PROCESS_0004", new String[]{callResponse.getMessage()});
        }
        if (callResponse.getData() == null || callResponse.getData().getContent() == null) {
            log.warn("\u672a\u83b7\u53d6\u5230\u6d41\u7a0b\u53c2\u6570\u914d\u7f6e, param:\u3010{}\u3011, message:\u3010{}\u3011", (Object)param, (Object)callResponse.getMessage());
            return null;
        }
        return (BpmPrefixForUdcResponseDto)callResponse.getData().getContent();
    }

    @Deprecated
    public BpmProcessLaunchResultDto startProcess(Object newData, Object oldData, Map<String, Object> extendMap) {
        String oldStatus;
        BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto = !extendMap.containsKey(BPM_PREFIX_PARAM_KEY) || extendMap.get(BPM_PREFIX_PARAM_KEY) == null ? this.getBpmPrefixParams(newData) : (BpmPrefixForUdcResponseDto)extendMap.get(BPM_PREFIX_PARAM_KEY);
        Map paramData = UdcReflectUtil.bean2Map((Object)oldData);
        Object billStatus = paramData.get("statusType");
        try {
            oldStatus = UdcReflectUtil.getEnumName(billStatus);
        }
        catch (Exception e) {
            log.error("\u83b7\u53d6\u65e7\u5355\u636e\u6570\u636e\u5355\u636e\u72b6\u6001\u679a\u4e3e\u503c\u5931\u8d25,oldData:\u3010{}\u3011", oldData);
            throw new BusinessException("BPM_PROCESS_0002");
        }
        String targetStatus = null;
        Map newDataMap = UdcReflectUtil.bean2Map((Object)newData);
        Object newBillStatus = newDataMap.get("statusType");
        try {
            targetStatus = UdcReflectUtil.getEnumName(newBillStatus);
        }
        catch (Exception e) {
            log.error("\u83b7\u53d6\u65b0\u5355\u636e\u6570\u636e\u5355\u636e\u72b6\u6001\u679a\u4e3e\u503c\u5931\u8d25,newData:\u3010{}\u3011", newData);
            throw new BusinessException("BPM_PROCESS_0003");
        }
        return this.startProcess0(newData, targetStatus, oldStatus, bpmPrefixForUdcResponseDto);
    }

    public BpmProcessLaunchResultDto startProcess0(Object newData, String targetStatus, String oldStatus, BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto) {
        if (bpmPrefixForUdcResponseDto == null) {
            log.warn("\u672a\u914d\u7f6e\u6d41\u7a0b\u6a21\u677f\u6216\u6839\u636e\u53c2\u6570\u672a\u67e5\u8be2\u5230\u6d41\u7a0b\u6a21\u677f\uff0c\u65e0\u6cd5\u53d1\u9001\u6d41\u7a0b...");
            return null;
        }
        if (newData == null) {
            log.error("\u53d1\u9001bpm\u6d41\u7a0b,\u5355\u636e\u6570\u636e\u4e0d\u80fd\u4e3a\u7a7a !");
            throw new BusinessException("BPM_PROCESS_0001");
        }
        oldStatus = Objects.isNull(oldStatus) ? "" : oldStatus;
        Map newDataMap = UdcReflectUtil.bean2Map((Object)newData);
        log.info("\u53d1\u8d77\u6d41\u7a0b\u72b6\u6001\u673a\uff1aoldStatus : \u3010{}\u3011 ,targetStatus: \u3010{}\u3011 ", (Object)oldStatus, (Object)targetStatus);
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = null;
        block8 : switch (oldStatus = Objects.isNull(oldStatus) ? "" : oldStatus) {
            case "PENDING_REVIEW": {
                switch (targetStatus) {
                    case "PENDING_REVIEW": {
                        bpmProcessLaunchResultDto = this.sendProcess(newData, newDataMap, bpmPrefixForUdcResponseDto);
                        break block8;
                    }
                }
                break;
            }
            case "DRAFT": {
                switch (targetStatus) {
                    case "PENDING_REVIEW": {
                        bpmProcessLaunchResultDto = this.sendProcess(newData, newDataMap, bpmPrefixForUdcResponseDto);
                        break block8;
                    }
                    case "DRAFT": 
                    case "TO_BE_SUBMITTED": {
                        bpmProcessLaunchResultDto = this.saveDraft(newData, newDataMap, bpmPrefixForUdcResponseDto);
                        break block8;
                    }
                }
                break;
            }
            case "TO_BE_SUBMITTED": 
            case "NONE": 
            case "": {
                switch (targetStatus) {
                    case "PENDING_REVIEW": {
                        bpmProcessLaunchResultDto = this.sendProcess(newData, newDataMap, bpmPrefixForUdcResponseDto);
                        break block8;
                    }
                    case "DRAFT": {
                        bpmProcessLaunchResultDto = this.saveDraft(newData, newDataMap, bpmPrefixForUdcResponseDto);
                        break block8;
                    }
                }
                break;
            }
        }
        if (bpmProcessLaunchResultDto != null) {
            try {
                this.updateBpmProcessAttribute(newData, bpmProcessLaunchResultDto);
            }
            catch (Exception e) {
                log.error("\u66f4\u65b0\u6d41\u7a0b\u5c5e\u6027\u5931\u8d25, newData:\u3010{}\u3011 , attributes:\u3010{}\u3011", newData, bpmProcessLaunchResultDto);
            }
        } else {
            log.debug("\u672a\u53d1\u8d77\u6d41\u7a0b\u6216\u8349\u7a3f,oldStatus:\u3010{}\u3011 , newStatus:\u3010{}\u3011", (Object)oldStatus, (Object)targetStatus);
        }
        return bpmProcessLaunchResultDto;
    }

    private BpmProcessLaunchResultDto sendProcess(Object data, Map<String, Object> dataMap, BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto) {
        log.info("\u5f00\u59cb\u53d1\u8d77\u6d41\u7a0b data:\u3010{}\u3011", dataMap);
        Long dataId = Long.parseLong(dataMap.get("id").toString());
        BpmSendUdcDto bpmSendUdcDto = new BpmSendUdcDto();
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = Optional.ofNullable(bpmPrefixForUdcResponseDto).map(bpmResult -> {
            SingleResponse response;
            BpmProcessLaunchResultDto resultDto = new BpmProcessLaunchResultDto();
            Long templateId = (Long)Nullable.ofNullable(dataMap.get("templateId")).ofLong().orElse((Object)0L);
            templateId = templateId == 0L ? bpmResult.getTemplateId() : templateId;
            resultDto.setTemplateId(templateId);
            Long caseId = null;
            Object caseIdObj = dataMap.get("caseId");
            if (caseIdObj != null) {
                caseId = Long.parseLong(caseIdObj.toString());
            }
            List paramPathNames = bpmResult.getParamPathNames();
            Map processParamMap = BpmDataUtil.filterMapData((Map)dataMap, (List)paramPathNames);
            bpmSendUdcDto.setTemplateId(templateId);
            bpmSendUdcDto.setRootEntityName(this.getEntityFullName(data));
            bpmSendUdcDto.setUserId(RequestContext.get().getUserId());
            bpmSendUdcDto.setFormRecordId(dataId);
            bpmSendUdcDto.setCaseId(caseId);
            bpmSendUdcDto.setFormData(processParamMap);
            BpmCommentDto bpmComment = this.getBpmComment(dataMap);
            bpmSendUdcDto.setCommentDto(bpmComment);
            bpmSendUdcDto.setCommentRequired(this.getCommentRequired(dataMap));
            List<ChangeNodeRequestDto> changeNodeRequestList = this.getChangeNodeRequest(dataMap);
            bpmSendUdcDto.setChangeNodeRequestDtos(changeNodeRequestList);
            PreMatchRequestDto preMatchRequestDto = this.getPreMatchRequestDto(dataMap);
            bpmSendUdcDto.setPreMatchRequestDto(preMatchRequestDto);
            bpmSendUdcDto.setApplicationName(Apps.getAppName());
            bpmSendUdcDto.setCommandId(String.valueOf(dataId));
            bpmSendUdcDto.setAffairId(this.getAffairId(data));
            try {
                log.info("\u53d1\u9001bpm\u6d41\u7a0b\uff0c\u53c2\u6570: \u3010{}\u3011", (Object)bpmSendUdcDto);
                response = this.bpmUdcApiService.sendForUdc(SingleRequest.from((Object)bpmSendUdcDto));
                log.info("\u53d1\u9001bpm\u6d41\u7a0b\uff0cbpm\u54cd\u5e94: \u3010{}\u3011", (Object)response);
                UdcReflectUtil.setEnumFiled((Object)data, (String)"sendState", (String)"SEND_SUCCESS");
                if (this.errorResponse(response)) {
                    if (response.getCode().equals("BOOT_1004")) {
                        throw new BusinessException("BOOT_1004");
                    }
                    log.error("\u53d1\u8d77\u6d41\u7a0b\u4e1a\u52a1\u5f02\u5e38 params:\u3010{}\u3011 , message:\u3010{}\u3011", (Object)bpmSendUdcDto, (Object)response.getMessage());
                    throw new BusinessException("BPM_PROCESS_0004", new String[]{response.getMessage()});
                }
            }
            catch (BusinessException e) {
                throw e;
            }
            catch (Exception e) {
                log.error("\u53d1\u9001\u6d41\u7a0brpc\u8c03\u7528\u5931\u8d25\u5373\u5c06\u8fdb\u5165\u91cd\u8bd5\u961f\u5217, bpmSendUdcDto:\u3010{}\u3011", (Object)bpmSendUdcDto);
                UdcReflectUtil.setEnumFiled((Object)data, (String)"sendState", (String)"SENDING");
                this.bpmRetryService.enqueue(data, (Map)Optional.ofNullable(dataMap.get("extraParamMap")).orElseGet(() -> new HashMap()));
                throw e;
            }
            BpmApiSendApiResponseDto content = (BpmApiSendApiResponseDto)response.getData().getContent();
            log.info("\u8c03\u7528bpm\u6d41\u7a0b\u53d1\u8d77\uff0c\u8fd4\u56de\u7ed3\u679c:\u3010{}\u3011", (Object)content);
            if (content.getPreMatchResponseDto() != null && content.getPreMatchResponseDto().isPop()) {
                UdcReflectUtil.setEnumFiled((Object)data, (String)"statusType", (String)"TO_BE_SUBMITTED");
                log.info("\u9700\u8981\u9009\u4eba\uff0c\u66f4\u65b0\u5355\u636e\u72b6\u6001\u4e3a\uff1aTO_BE_SUBMITTED");
            }
            resultDto.setCaseId(content.getCaseId());
            resultDto.setPreMatchResponseDto(content.getPreMatchResponseDto());
            resultDto.setCaseSender(content.getSenderId());
            resultDto.setCaseSenderDepartment(content.getSenderDepartmentId());
            resultDto.setCaseSenderInstitution(content.getSenderInstitutionId());
            resultDto.setCaseSenderPost(content.getSenderPostId());
            resultDto.setCaseTitle(content.getSubject());
            resultDto.setCaseState(content.getCaseState());
            resultDto.setApprovalState(content.getApprovalState());
            resultDto.setCaseStartTime(content.getCaseStartTime());
            resultDto.setErrorMsg(content.getErrorMsg());
            resultDto.setProcessType(content.getProcessType());
            return resultDto;
        }).orElseGet(() -> {
            log.info("\u672a\u83b7\u53d6\u5230\u6d41\u7a0b\u53c2\u6570\u914d\u7f6e,\u4e0d\u8c03\u7528\u5de5\u4f5c\u6d41\u53d1\u8d77\u63a5\u53e3,entityFullName:{},dataId:{}", (Object)this.getEntityFullName(data), (Object)dataId);
            BpmProcessLaunchResultDto resultDto = new BpmProcessLaunchResultDto();
            resultDto.setTemplateId(UdcCommonConstant.NULL_ID);
            resultDto.setCaseId(UdcCommonConstant.NULL_ID);
            return resultDto;
        });
        return bpmProcessLaunchResultDto;
    }

    private Long getAffairId(Object newData) {
        Long affairId = null;
        Map extraParamMap = ((BaseRootDto)newData).getExtraParamMap();
        if (MapUtils.isNotEmpty((Map)extraParamMap)) {
            affairId = (Long)Nullable.ofNullable(extraParamMap.get("affairId")).ofLong().get();
        }
        return affairId;
    }

    private boolean isMainProcess(BpmProcessLaunchResultDto dto) {
        return dto == null || dto.getProcessType() == null || dto.getProcessType() == CaseTypeEnum.MAIN_PROCESS;
    }

    private String getEntityFullName(Object data) {
        return Optional.ofNullable(data.getClass().getAnnotation(DtoInfo.class)).map(DtoInfo::entity).orElse("");
    }

    private BpmProcessLaunchResultDto saveDraft(Object data, Map<String, Object> paramData, BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto) {
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = new BpmProcessLaunchResultDto();
        Long dataId = Long.parseLong(paramData.get("id").toString());
        Long templateId = (Long)Nullable.ofNullable((Object)paramData.get("templateId")).ofLong().orElse((Object)0L);
        templateId = templateId == 0L ? bpmPrefixForUdcResponseDto.getTemplateId() : templateId;
        Long caseId = null;
        Object caseIdObj = paramData.get("caseId");
        if (caseIdObj != null) {
            caseId = Long.parseLong(caseIdObj.toString());
        }
        List paramPathNames = bpmPrefixForUdcResponseDto.getParamPathNames();
        Map processParamMap = BpmDataUtil.filterMapData(paramData, (List)paramPathNames);
        BpmSaveDraftUdcDto bpmSaveDraftUdcDto = new BpmSaveDraftUdcDto();
        bpmSaveDraftUdcDto.setTemplateId(templateId);
        bpmSaveDraftUdcDto.setRootEntityName(this.getEntityFullName(data));
        bpmSaveDraftUdcDto.setUserId(RequestContext.get().getUserId());
        bpmSaveDraftUdcDto.setFormRecordId(dataId);
        bpmSaveDraftUdcDto.setFormData(processParamMap);
        Map extraParamMap = MapUtils.getMap(paramData, (Object)"extraParamMap");
        bpmSaveDraftUdcDto.setPageUrl(MapUtils.getString((Map)extraParamMap, (Object)"pageUrl"));
        String pageType = MapUtils.getString((Map)extraParamMap, (Object)"pageType");
        if (StringUtils.isNotEmpty((CharSequence)pageType)) {
            bpmSaveDraftUdcDto.setPageType(PageTypeEnum.valueOf((String)pageType));
        }
        bpmSaveDraftUdcDto.setPageGuid(MapUtils.getLong((Map)extraParamMap, (Object)"pageGuid"));
        BpmCommentDto bpmComment = this.getBpmComment(paramData);
        bpmSaveDraftUdcDto.setCommentDto(bpmComment);
        bpmSaveDraftUdcDto.setBpmOperationNodeDto(this.getBpmOperationNodeDto(paramData));
        bpmSaveDraftUdcDto.setCommandId(String.valueOf(dataId));
        bpmSaveDraftUdcDto.setAffairId(this.getAffairId(data));
        SingleResponse draftResponse = this.bpmUdcApiService.saveDraft(SingleRequest.from((Object)bpmSaveDraftUdcDto));
        if (!draftResponse.success()) {
            if (draftResponse.getCode().equals("BOOT_1004")) {
                throw new BusinessException("BOOT_1004");
            }
            log.error("\u53d1\u9001\u6d41\u7a0b\u8349\u7a3f,dubbo \u8c03\u7528\u53c2\u6570:\u3010{}\u3011 , message:\u3010{}\u3011 ", (Object)bpmSaveDraftUdcDto, (Object)draftResponse.getMessage());
            throw new BusinessException("BPM_PROCESS_0004", new String[]{draftResponse.getMessage()});
        }
        if (draftResponse.getData() != null && draftResponse.getData().getContent() != null) {
            BpmSaveDraftUdcResponseDto content = (BpmSaveDraftUdcResponseDto)draftResponse.getData().getContent();
            log.debug("\u4fdd\u5b58\u6d41\u7a0b\u8349\u7a3f\uff0cresponse:\u3010{}\u3011", (Object)content);
            bpmProcessLaunchResultDto.setCaseId(content.getCaseId());
            bpmProcessLaunchResultDto.setCaseSender(content.getMemberId());
            bpmProcessLaunchResultDto.setCaseSenderInstitution(content.getAccountId());
            bpmProcessLaunchResultDto.setCaseSenderDepartment(content.getDepartmentId());
            bpmProcessLaunchResultDto.setCaseSenderPost(content.getPostId());
            bpmProcessLaunchResultDto.setTemplateId(content.getTemplateId());
            bpmProcessLaunchResultDto.setAffairId(content.getAffairId());
            bpmProcessLaunchResultDto.setProcessType(content.getProcessType());
            bpmProcessLaunchResultDto.setCaseTitle(content.getSubject());
        } else {
            log.warn("\u53d1\u9001\u6d41\u7a0b\u8349\u7a3f\u672a\u8fd4\u56decaseId, dubbo \u8c03\u7528\u53c2\u6570:\u3010{}\u3011 , message:\u3010{}\u3011 ", (Object)bpmSaveDraftUdcDto, (Object)draftResponse.getMessage());
            bpmProcessLaunchResultDto.setCaseId(caseId);
        }
        return bpmProcessLaunchResultDto;
    }

    private BpmProcessLaunchResultDto repealProcess(Object data, BpmPrefixForUdcResponseDto bpmPrefixForUdcResponseDto) {
        BpmProcessLaunchResultDto bpmProcessLaunchResultDto = new BpmProcessLaunchResultDto();
        BpmOperationRepealUdcDto repealUdcDto = new BpmOperationRepealUdcDto();
        Map paramData = UdcReflectUtil.bean2Map((Object)data);
        Long dataId = Long.parseLong(paramData.get("id").toString());
        Map processParamMap = BpmDataUtil.filterMapData((Map)paramData, (List)bpmPrefixForUdcResponseDto.getParamPathNames());
        Long caseId = null;
        Object caseIdObj = paramData.get("caseId");
        if (caseIdObj != null) {
            caseId = Long.parseLong(caseIdObj.toString());
        }
        repealUdcDto.setCaseId(caseId);
        repealUdcDto.setCommentDto(this.getBpmComment(paramData));
        repealUdcDto.setCommandId(String.valueOf(dataId));
        repealUdcDto.setParameterData(processParamMap);
        bpmProcessLaunchResultDto.setCaseId(caseId);
        bpmProcessLaunchResultDto.setTemplateId(bpmPrefixForUdcResponseDto.getTemplateId());
        SingleResponse response = this.bpmUdcApiService.repealForUdc(SingleRequest.from((Object)repealUdcDto));
        if (response.getStatus() != 0) {
            log.error("\u64a4\u9500\u6d41\u7a0b\u5931\u8d25 ,  data:\u3010{}\u3011 , message:\u3010{}\u3011", data, (Object)response.getMessage());
            throw new BusinessException("BPM_PROCESS_0006", new String[]{response.getMessage()});
        }
        return bpmProcessLaunchResultDto;
    }

    private BpmCommentDto getBpmComment(Map<String, Object> dataMap) {
        Map billExtraMap = (Map)Optional.ofNullable(dataMap.get("extraParamMap")).orElseGet(() -> Collections.emptyMap());
        log.info("\u83b7\u53d6\u9644\u8a00\u4fe1\u606f extraParamMap\uff1a\u3010{}\u3011", (Object)billExtraMap);
        Object bpmComment = billExtraMap.get(BPM_COMMENT);
        if (bpmComment != null) {
            log.info("bpmComment type:\u3010{}\u3011", bpmComment.getClass());
            if (bpmComment instanceof Map) {
                return this.getBpmCommentDtoResult(bpmComment);
            }
            if (bpmComment instanceof String) {
                Map paramMap = UdcJsonUtils.toMap((String)((String)bpmComment));
                return this.getBpmCommentDtoResult(paramMap);
            }
            log.error("\u9644\u8a00\u4fe1\u606f\u7c7b\u578b: \u3010{}\u3011", bpmComment.getClass());
        }
        return null;
    }

    private boolean getCommentRequired(Map<String, Object> dataMap) {
        Map billExtraMap = (Map)Optional.ofNullable(dataMap.get("extraParamMap")).orElseGet(() -> Collections.emptyMap());
        log.info("\u83b7\u53d6\u9644\u8a00\u5fc5\u586b\u4fe1\u606f extraParamMap\uff1a\u3010{}\u3011", (Object)billExtraMap);
        return MapUtils.getBoolean((Map)billExtraMap, (Object)"commentRequired", (Boolean)false);
    }

    private BpmOperationNodeDto getBpmOperationNodeDto(Map<String, Object> paramData) {
        Map bpmOperationNodeDtoMap;
        Map billExtraMap = (Map)Optional.ofNullable(paramData.get("extraParamMap")).orElseGet(() -> Collections.emptyMap());
        if (MapUtil.isNotEmpty((Map)billExtraMap) && MapUtil.isNotEmpty((Map)(bpmOperationNodeDtoMap = Optional.ofNullable(billExtraMap.get("bpmOperationNodeDto")).map(e -> (Map)e).orElse(Maps.newHashMap())))) {
            log.info("\u83b7\u53d6\u64cd\u4f5c\u8282\u70b9\u4fe1\u606f:\u3010{}\u3011", (Object)bpmOperationNodeDtoMap);
            return (BpmOperationNodeDto)UdcJsonUtils.fromJson((String)UdcJsonUtils.toJson((Object)bpmOperationNodeDtoMap), BpmOperationNodeDto.class);
        }
        return null;
    }

    private BpmCommentDto getBpmCommentDtoResult(Object bpmComment) {
        Object attachmentStorageIds = ((Map)bpmComment).get(ATTACHMENT_STORAGEIDS);
        if (attachmentStorageIds != null && attachmentStorageIds instanceof Collection && CollectionUtils.isNotEmpty((Collection)((Collection)attachmentStorageIds))) {
            List fileList = ((Collection)attachmentStorageIds).stream().map(e -> {
                log.info("\u8f6c\u6362\u9644\u8a00\u9644\u4ef6\u4fe1\u606f , e:\u3010{}\u3011", e);
                return (Map)e;
            }).collect(Collectors.toList());
            ((Map)bpmComment).put(ATTACHMENT_STORAGEIDS, fileList);
        }
        log.info("\u6784\u5efa\u9644\u8a00\u53d1\u9001\u6570\u636e:\u3010{}\u3011", bpmComment);
        return (BpmCommentDto)UdcJsonUtils.fromJson((String)UdcJsonUtils.toJson((Object)bpmComment), BpmCommentDto.class);
    }

    private List<ChangeNodeRequestDto> getChangeNodeRequest(Map<String, Object> dataMap) {
        ArrayList<ChangeNodeRequestDto> list = new ArrayList<ChangeNodeRequestDto>();
        Map billExtraMap = (Map)Optional.ofNullable(dataMap.get("extraParamMap")).orElseGet(() -> new HashMap());
        Object signs = billExtraMap.get("changeNodeRequestDtos");
        if (signs != null) {
            log.info("\u5904\u7406\u52a0\u7b7e\u3001\u51cf\u7b7e\u5185\u5bb9: \u3010{}\u3011", signs);
            if (signs instanceof Collection) {
                log.info("\u96c6\u5408\u5904\u7406");
                for (Object sign : (Collection)signs) {
                    ChangeNodeRequestDto changeNodeRequestDto = (ChangeNodeRequestDto)UdcJsonUtils.fromJson((String)UdcJsonUtils.toJson(sign), ChangeNodeRequestDto.class);
                    list.add(changeNodeRequestDto);
                }
            }
        }
        return list;
    }

    private PreMatchRequestDto getPreMatchRequestDto(Map<String, Object> paramData) {
        Map billExtraMap = (Map)Optional.ofNullable(paramData.get("extraParamMap")).orElseGet(() -> new HashMap());
        Object preMatch = billExtraMap.get(PRE_MATCH_REQUEST_DTO);
        if (preMatch != null) {
            if (preMatch instanceof String) {
                return (PreMatchRequestDto)UdcJsonUtils.fromJson((String)((String)preMatch), PreMatchRequestDto.class);
            }
            return (PreMatchRequestDto)UdcJsonUtils.fromJson((String)UdcJsonUtils.toJson(preMatch), PreMatchRequestDto.class);
        }
        log.info("preMatchRequestDto \u4e3a\u7a7a!");
        return null;
    }

    private void updateBpmProcessAttribute(Object newData, BpmProcessLaunchResultDto bpmProcessLaunchResultDto) {
        log.debug("\u4fee\u6539\u5355\u636e\u5c5e\u6027\uff0cnewData:\u3010{}\u3011", newData);
        Long caseId = bpmProcessLaunchResultDto.getCaseId();
        if (Objects.isNull(caseId) || caseId == 0L) {
            throw BusinessException.message((String)"BPM \u54cd\u5e94\u6d41\u7a0b\u5b9e\u4f8bid\u4e3a\u7a7a!");
        }
        Long templateId = bpmProcessLaunchResultDto.getTemplateId();
        Long caseSender = bpmProcessLaunchResultDto.getCaseSender();
        Long caseSenderDepartment = bpmProcessLaunchResultDto.getCaseSenderDepartment();
        Long caseSenderInstitution = bpmProcessLaunchResultDto.getCaseSenderInstitution();
        Long caseSenderPost = bpmProcessLaunchResultDto.getCaseSenderPost();
        String caseTitle = bpmProcessLaunchResultDto.getCaseTitle();
        Long caseStartTime = bpmProcessLaunchResultDto.getCaseStartTime();
        UdcReflectUtil.setFieldValue((Object)newData, (String)"caseId", (Object)caseId);
        Optional.ofNullable(templateId).ifPresent(item -> UdcReflectUtil.setFieldValue((Object)newData, (String)"templateId", (Object)templateId));
        Optional.ofNullable(caseSender).ifPresent(item -> {
            Object case_sender = UdcReflectUtil.getFieldValue((Object)newData, (String)"caseSender");
            if (Objects.isNull(case_sender) || Objects.equals(case_sender, UdcCommonConstant.NULL_ID)) {
                UdcReflectUtil.setFieldValue((Object)newData, (String)"caseSender", (Object)caseSender);
            }
        });
        Optional.ofNullable(caseSenderDepartment).ifPresent(item -> {
            Object case_sender_department = UdcReflectUtil.getFieldValue((Object)newData, (String)"caseSenderDepartment");
            if (Objects.isNull(case_sender_department) || Objects.equals(case_sender_department, UdcCommonConstant.NULL_ID)) {
                UdcReflectUtil.setFieldValue((Object)newData, (String)"caseSenderDepartment", (Object)caseSenderDepartment);
            }
        });
        Optional.ofNullable(caseSenderInstitution).ifPresent(item -> {
            Object case_sender_institution = UdcReflectUtil.getFieldValue((Object)newData, (String)"caseSenderInstitution");
            if (Objects.isNull(case_sender_institution) || Objects.equals(case_sender_institution, UdcCommonConstant.NULL_ID)) {
                UdcReflectUtil.setFieldValue((Object)newData, (String)"caseSenderInstitution", (Object)caseSenderInstitution);
            }
        });
        Optional.ofNullable(caseSenderPost).ifPresent(item -> {
            Object case_sender_post = UdcReflectUtil.getFieldValue((Object)newData, (String)"caseSenderPost");
            if (Objects.isNull(case_sender_post) || Objects.equals(case_sender_post, UdcCommonConstant.NULL_ID)) {
                UdcReflectUtil.setFieldValue((Object)newData, (String)"caseSenderPost", (Object)caseSenderPost);
            }
        });
        Optional.ofNullable(caseTitle).ifPresent(item -> UdcReflectUtil.setFieldValue((Object)newData, (String)"caseTitle", (Object)caseTitle));
    }

    private boolean errorResponse(SingleResponse response) {
        return response == null || !response.success() || response.getData() == null || response.getData().getContent() == null;
    }
}
