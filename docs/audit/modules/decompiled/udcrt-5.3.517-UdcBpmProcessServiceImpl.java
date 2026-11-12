/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.AppService
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.context.SystemEnvironment
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.i18n.MessageRepository
 *  com.seeyon.boot.starter.udcrt.api.UdcBpmProcessService
 *  com.seeyon.boot.starter.udcrt.domain.service.BpmActionProcessingService
 *  com.seeyon.boot.starter.udcrt.domain.service.FormHandlerFactory
 *  com.seeyon.boot.starter.udcrt.dto.BpmParameterDataDto
 *  com.seeyon.boot.starter.udcrt.dto.DataValidBaseFilterDto
 *  com.seeyon.boot.starter.udcrt.dto.DataValidCreateFilterDto
 *  com.seeyon.boot.starter.udcrt.dto.DataValidUpdateFilterDto
 *  com.seeyon.boot.starter.udcrt.dto.FormParamDto
 *  com.seeyon.boot.starter.udcrt.util.BpmDataUtil
 *  com.seeyon.boot.starter.udcrt.util.UdcReflectUtil
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.util.Asserts
 *  com.seeyon.boot.util.JsonUtils
 *  com.seeyon.bpm.dto.message.BpmApprovalResultData
 *  com.seeyon.bpm.dto.message.event.BpmCancelEvent
 *  com.seeyon.bpm.dto.message.event.BpmStopEvent
 *  com.seeyon.udc.common.enums.ApplicationSourceEnum
 *  com.seeyon.udc.common.utils.ResponseUtils
 *  com.seeyon.udc.common.utils.UdcJsonUtils
 *  org.apache.commons.collections.MapUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.data.util.CastUtils
 */
package com.seeyon.boot.starter.udcrt.appservice;

import com.seeyon.boot.annotation.AppService;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.context.SystemEnvironment;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.i18n.MessageRepository;
import com.seeyon.boot.starter.udcrt.api.UdcBpmProcessService;
import com.seeyon.boot.starter.udcrt.domain.service.BpmActionProcessingService;
import com.seeyon.boot.starter.udcrt.domain.service.FormHandlerFactory;
import com.seeyon.boot.starter.udcrt.dto.BpmParameterDataDto;
import com.seeyon.boot.starter.udcrt.dto.DataValidBaseFilterDto;
import com.seeyon.boot.starter.udcrt.dto.DataValidCreateFilterDto;
import com.seeyon.boot.starter.udcrt.dto.DataValidUpdateFilterDto;
import com.seeyon.boot.starter.udcrt.dto.FormParamDto;
import com.seeyon.boot.starter.udcrt.util.BpmDataUtil;
import com.seeyon.boot.starter.udcrt.util.UdcReflectUtil;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.util.Asserts;
import com.seeyon.boot.util.JsonUtils;
import com.seeyon.bpm.dto.message.BpmApprovalResultData;
import com.seeyon.bpm.dto.message.event.BpmCancelEvent;
import com.seeyon.bpm.dto.message.event.BpmStopEvent;
import com.seeyon.udc.common.enums.ApplicationSourceEnum;
import com.seeyon.udc.common.utils.ResponseUtils;
import com.seeyon.udc.common.utils.UdcJsonUtils;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.apache.commons.collections.MapUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.CastUtils;

@AppService
public class UdcBpmProcessServiceImpl
implements UdcBpmProcessService {
    private static final Logger log = LoggerFactory.getLogger(UdcBpmProcessServiceImpl.class);
    private static final String VALIDATE_METHOD = "validate";
    private static final String UPDATE_METHOD = "update";
    private static final String UPDATE_WITHRESULT_METHOD = "updateWithResult";
    private static final String CREATE_WITHRESULT_METHOD = "createWithResult";
    @Autowired
    private MessageRepository messageRepository;
    @Autowired
    private BpmActionProcessingService bpmActionProcessingService;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private SingleResponse<BpmParameterDataDto> validFilterData(DataValidBaseFilterDto dataDto, String invokeMethod) {
        Object queryResultDto;
        block14: {
            Map data;
            if (log.isInfoEnabled()) {
                log.info("\u6d41\u7a0b\u5904\u7406\u65b9\u6cd5:{},\u6570\u636e\uff1a{}", (Object)invokeMethod, (Object)JsonUtils.toJson((Object)dataDto));
            }
            if (MapUtils.isNotEmpty((Map)(data = dataDto.getData()))) {
                Map extraParamMap = MapUtils.getMap((Map)data, (Object)"extraParamMap", new HashMap(2));
                extraParamMap.put("processActionSource", "bpm");
                data.put("extraParamMap", extraParamMap);
            }
            Asserts.notEmpty((String)dataDto.getAppName(), (String)"\u6240\u5c5e\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getDynamicAppName(), (String)"\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getRootEntityFullName(), (String)"\u6839\u5b9e\u4f53fullName");
            queryResultDto = null;
            try {
                boolean preFlag;
                HashSet<String> ignoreSet = new HashSet<String>();
                ignoreSet.add(dataDto.getRootEntityFullName());
                Apps.ignorePermission(ignoreSet);
                FormParamDto formParamDto = new FormParamDto();
                formParamDto.setJsonStrParam(UdcJsonUtils.toJson((Object)data));
                formParamDto.setArtifactId(dataDto.getDynamicAppName());
                formParamDto.setAggEntityFullName(dataDto.getRootEntityFullName());
                formParamDto.setInvokeMethod(invokeMethod);
                boolean bl = preFlag = Apps.getAppName().equals(dataDto.getAppName()) || Apps.isMonolithic() || SystemEnvironment.isSandbox();
                if (preFlag && dataDto.getDynamicAppName().startsWith("dynamic")) {
                    SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.FORM).dataProcess(formParamDto);
                    Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                    if (!optional.isPresent()) {
                        SingleResponse singleResponse = response;
                        return singleResponse;
                    }
                    queryResultDto = optional.get();
                    break block14;
                }
                if (preFlag && !dataDto.getDynamicAppName().startsWith("dynamic")) {
                    SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.NORMAL).dataProcess(formParamDto);
                    Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                    if (!optional.isPresent()) {
                        SingleResponse singleResponse = response;
                        return singleResponse;
                    }
                    queryResultDto = optional.get();
                    break block14;
                }
                throw new BusinessException().addError("\u4e0d\u652f\u6301\u7684\u73af\u5883");
            }
            catch (Exception e) {
                SingleResponse response;
                log.error("error", (Throwable)e);
                SingleResponse singleResponse = response = this.getErrorResponse(e);
                return singleResponse;
            }
            finally {
                Apps.ignorePermissionFinish();
            }
        }
        Map dbMap = UdcReflectUtil.bean2Map(queryResultDto);
        Map processFilterParam = BpmDataUtil.filterMapData((Map)dbMap, (List)dataDto.getPathNames());
        if (log.isInfoEnabled()) {
            log.info("{},\u8fc7\u6ee4\u6570\u636e:{}", (Object)invokeMethod, (Object)JsonUtils.toJson((Object)processFilterParam));
        }
        return SingleResponse.from((Object)BpmParameterDataDto.builder().formData(dbMap).parameterData(processFilterParam).build());
    }

    public SingleResponse<BpmParameterDataDto> validUpdateFilterData(SingleRequest<DataValidUpdateFilterDto> request) {
        return this.validFilterData((DataValidBaseFilterDto)request.getData(), UPDATE_WITHRESULT_METHOD);
    }

    public SingleResponse<BpmParameterDataDto> validCreateFilterData(SingleRequest<DataValidCreateFilterDto> request) {
        return this.validFilterData((DataValidBaseFilterDto)request.getData(), CREATE_WITHRESULT_METHOD);
    }

    public SingleResponse<BpmParameterDataDto> validFilterData(SingleRequest<DataValidUpdateFilterDto> request) {
        Object queryResultDto;
        DataValidUpdateFilterDto dataDto;
        block7: {
            dataDto = (DataValidUpdateFilterDto)request.getData();
            Optional.ofNullable(dataDto.getData()).ifPresent(map -> map.put("actionType", dataDto.getActionType()));
            if (log.isInfoEnabled()) {
                log.info("\u6d41\u7a0b\u5904\u7406\u6570\u636e\uff1a{}", (Object)JsonUtils.toJson((Object)dataDto));
            }
            Map data = dataDto.getData();
            Asserts.notEmpty((String)dataDto.getAppName(), (String)"\u6240\u5c5e\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getDynamicAppName(), (String)"\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getRootEntityFullName(), (String)"\u6839\u5b9e\u4f53fullName");
            queryResultDto = null;
            try {
                boolean preFlag;
                FormParamDto formParamDto = new FormParamDto();
                formParamDto.setJsonStrParam(UdcJsonUtils.toJson((Object)data));
                formParamDto.setArtifactId(dataDto.getDynamicAppName());
                formParamDto.setAggEntityFullName(dataDto.getRootEntityFullName());
                formParamDto.setInvokeMethod(VALIDATE_METHOD);
                boolean bl = preFlag = Apps.getAppName().equals(dataDto.getAppName()) || Apps.isMonolithic();
                if (preFlag && dataDto.getDynamicAppName().startsWith("dynamic")) {
                    SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.FORM).dataProcess(formParamDto);
                    Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                    if (optional.isPresent()) {
                        queryResultDto = optional.get();
                        break block7;
                    }
                    return response;
                }
                if (!preFlag || dataDto.getDynamicAppName().startsWith("dynamic")) break block7;
                SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.NORMAL).dataProcess(formParamDto);
                Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                if (optional.isPresent()) {
                    queryResultDto = optional.get();
                    break block7;
                }
                return response;
            }
            catch (Exception e) {
                log.error("error", (Throwable)e);
                SingleResponse response = this.getErrorResponse(e);
                return response;
            }
        }
        Map dbMap = UdcReflectUtil.bean2Map(queryResultDto);
        Map processFilterParam = BpmDataUtil.filterMapData((Map)dbMap, (List)dataDto.getPathNames());
        if (log.isInfoEnabled()) {
            log.info("validFilterData\u8fc7\u6ee4\u6570\u636e:{}", (Object)JsonUtils.toJson((Object)processFilterParam));
        }
        return SingleResponse.from((Object)BpmParameterDataDto.builder().parameterData(processFilterParam).build());
    }

    public SingleResponse updateData(SingleRequest<DataValidUpdateFilterDto> request) {
        Object queryResultDto;
        block6: {
            DataValidUpdateFilterDto dataDto = (DataValidUpdateFilterDto)request.getData();
            if (log.isInfoEnabled()) {
                log.info("\u6d41\u7a0b\u66f4\u65b0\u6570\u636e\uff1a{}", (Object)JsonUtils.toJson((Object)dataDto));
            }
            Map data = dataDto.getData();
            Asserts.notEmpty((String)dataDto.getAppName(), (String)"\u6240\u5c5e\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getDynamicAppName(), (String)"\u5e94\u7528\u540d\u79f0");
            Asserts.notEmpty((String)dataDto.getRootEntityFullName(), (String)"\u6839\u5b9e\u4f53fullName");
            queryResultDto = null;
            try {
                boolean preFlag;
                FormParamDto formParamDto = new FormParamDto();
                formParamDto.setJsonStrParam(UdcJsonUtils.toJson((Object)data));
                formParamDto.setArtifactId(dataDto.getDynamicAppName());
                formParamDto.setAggEntityFullName(dataDto.getRootEntityFullName());
                formParamDto.setInvokeMethod(UPDATE_METHOD);
                boolean bl = preFlag = Apps.getAppName().equals(dataDto.getAppName()) || Apps.isMonolithic();
                if (preFlag && dataDto.getDynamicAppName().startsWith("dynamic")) {
                    SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.FORM).dataProcess(formParamDto);
                    Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                    if (optional.isPresent()) {
                        queryResultDto = optional.get();
                        break block6;
                    }
                    return response;
                }
                if (!preFlag || dataDto.getDynamicAppName().startsWith("dynamic")) break block6;
                SingleResponse response = (SingleResponse)FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.NORMAL).dataProcess(formParamDto);
                Optional optional = ResponseUtils.ofNullable((SingleResponse)response);
                if (optional.isPresent()) {
                    queryResultDto = optional.get();
                    break block6;
                }
                return response;
            }
            catch (Exception e) {
                log.error("error", (Throwable)e);
                SingleResponse response = this.getErrorResponse(e);
                return response;
            }
        }
        return SingleResponse.from(queryResultDto);
    }

    public SingleResponse<Boolean> processBpmApproval(SingleRequest<BpmApprovalResultData> request) {
        return SingleResponse.from((Object)this.bpmActionProcessingService.processApprovalAction((BpmApprovalResultData)request.getData(), false));
    }

    public SingleResponse<Boolean> processBpmStop(SingleRequest<BpmStopEvent> request) {
        return SingleResponse.from((Object)this.bpmActionProcessingService.processBpmStopAction((BpmStopEvent)request.getData()));
    }

    public SingleResponse<Boolean> processBpmCancel(SingleRequest<BpmCancelEvent> request) {
        return SingleResponse.from((Object)this.bpmActionProcessingService.processBpmCancelAction((BpmCancelEvent)request.getData()));
    }

    public SingleResponse<Boolean> processBpmTakeBack(SingleRequest<BpmApprovalResultData> request) {
        return SingleResponse.from((Object)this.bpmActionProcessingService.processApprovalAction((BpmApprovalResultData)request.getData(), true));
    }

    private SingleResponse getErrorResponse(Exception e) {
        SingleResponse response = new SingleResponse();
        response.setStatus(2);
        response.setCode("PROCESS_0002");
        if (e instanceof BusinessException) {
            BusinessException businessException = (BusinessException)CastUtils.cast((Object)e);
            if (Objects.nonNull(businessException.getMessage())) {
                response.setMessage(businessException.getMessage());
            } else {
                String code = businessException.code();
                String errorMsg = this.messageRepository.getMessage("error.code." + code, businessException.getParams());
                response.setMessage(errorMsg);
            }
        } else {
            response.setMessage(e.getMessage());
        }
        return response;
    }
}
