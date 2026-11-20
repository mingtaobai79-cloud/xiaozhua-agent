package com.seeyon.datamigration163126498398523384.custom.appservice.microflow;

import com.seeyon.boot.transport.*;
import com.seeyon.boot.annotation.AppService;
import com.seeyon.boot.annotation.AppServiceOperation;
import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.OpenApi;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.datamigration163126498398523384.api.microflow.CustomMicroFlowAppService;
import com.seeyon.datamigration163126498398523384.custom.service.microflow.CustomMicroFlowService;
import com.seeyon.udc.common.constant.MicroFlowCommonConstant;
import org.apache.dubbo.config.annotation.DubboService;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * CustomMicroFlowAppService 默认实现类
 */
@AppService(value = "DefaultCustomMicroFlowAppServiceImpl",
        customs = {
                @Custom(properties = @CustomAttribute(name = MicroFlowCommonConstant.APP_SERVICE_ANNOTATION_CUSTOM_KEY, value = "true")),
                @Custom(properties = @CustomAttribute(name = "isDefault", value = "true"))
        }
)
public class DefaultCustomMicroFlowAppServiceImpl implements CustomMicroFlowAppService {

    private CustomMicroFlowService customMicroFlowService;

    @Autowired(required = false)
    public void setCustomMicroFlowService(CustomMicroFlowService customMicroFlowService) {
        this.customMicroFlowService = customMicroFlowService;
    }

    @Override
    @AppServiceOperation(value = "P0-自定义定时验证"
            , description = ""
            , openApi = @OpenApi(isOpenApi = false)
            , customs = {
                      @Custom(properties = @CustomAttribute(name = "mfId", value = "7674299753416331984")), 
@Custom(properties = @CustomAttribute(name = "mfTriggerType", value = "SCHEDULE"))
              })
    public SingleResponse<Void> p0CustomScheduleProbe(){
        if(customMicroFlowService == null){
            throw new BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
        }
        customMicroFlowService.p0CustomScheduleProbe();
        return SingleResponse.ok();
    }
    @Override
    @AppServiceOperation(value = "P0-自定义事件监听验证"
            , description = ""
            , openApi = @OpenApi(isOpenApi = false)
            , customs = {
                      @Custom(properties = @CustomAttribute(name = "mfId", value = "4620867461310390367")), 
@Custom(properties = @CustomAttribute(name = "mfTriggerType", value = "BUSINESS_EVENT"))
              })
    public SingleResponse<Void> p0CustomEventProbe(@com.seeyon.boot.annotation.ParameterInfo("事件数据") SingleRequest<com.seeyon.udc.common.event.BeforeCreateEvent<com.seeyon.datamigration163126498398523384.dto.AeProbeEntityDto>> request){
        if(customMicroFlowService == null){
            throw new BusinessException(com.seeyon.boot.starter.udcrt.exception.MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
        }
        customMicroFlowService.p0CustomEventProbe(request.getData());
        return SingleResponse.ok();
    }
}
