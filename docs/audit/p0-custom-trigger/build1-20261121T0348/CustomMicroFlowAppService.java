package com.seeyon.datamigration163126498398523384.api.microflow;

import com.seeyon.boot.transport.*;

import java.util.List;
import java.util.Map;

/**
 * 自定义微流程 AppService 接口
 */
public interface CustomMicroFlowAppService {

        /**
         * P0-自定义定时验证
         * 
         */
        default SingleResponse<Void> p0CustomScheduleProbe() {
            throw new com.seeyon.boot.exception.BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_UNIMPLEMENTED_METHOD);
        }
        /**
         * P0-自定义事件监听验证
         * 
         */
        default SingleResponse<Void> p0CustomEventProbe() {
            throw new com.seeyon.boot.exception.BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_UNIMPLEMENTED_METHOD);
        }
}