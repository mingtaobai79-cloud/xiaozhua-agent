package com.seeyon.datamigration163126498398523384.custom.service.microflow;

import com.seeyon.boot.transport.*;
import java.util.List;
import java.util.Map;

/**
 * 自定义微流程 AppService 接口
 */
public interface CustomMicroFlowService {

    default void p0CustomScheduleProbe( ) {
        throw new com.seeyon.boot.exception.BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_UNIMPLEMENTED_METHOD);
    }
    default void p0CustomEventProbe(com.seeyon.udc.common.event.BeforeCreateEvent<com.seeyon.datamigration163126498398523384.dto.AeProbeEntityDto> _BUSINESS_EVENT_ka3rXs) {
        throw new com.seeyon.boot.exception.BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_UNIMPLEMENTED_METHOD);
    }
}