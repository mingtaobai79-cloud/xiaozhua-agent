package com.seeyon.datamigration163126498398523384.domain.event.listener.microflow;



import com.seeyon.datamigration163126498398523384.api.microflow.CustomMicroFlowAppService;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.udc.common.event.BeforeCreateEvent;
import com.seeyon.boot.starter.eventbus.annotation.EventHandler;
import com.seeyon.boot.starter.eventbus.annotation.EventSubscribe;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import com.seeyon.boot.starter.udcrt.util.MicroFlowLogUtil;
import org.springframework.transaction.annotation.Propagation;

/**
 * P0-自定义事件监听验证
 * @author seeyon
 * @date 2026-11-21 03:48:35
 * @since 1.0.0
 */
@Slf4j
@EventHandler
@org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class,propagation = Propagation.REQUIRED)
public class P0CustomEventProbeListener {
    @Autowired(required = false)
    private CustomMicroFlowAppService customMicroFlowAppService;


    @EventSubscribe
    public void onBeforeCreateEvent(BeforeCreateEvent<com.seeyon.datamigration163126498398523384.dto.AeProbeEntityDto> aeProbeEntitycomseeyonudccommoneventBeforeCreateEvent) {
        com.seeyon.boot.starter.udcrt.util.MicroFlowRuntimeUtil.saveDefaultValue4RequestContext();
            log.info("接收到“接口验证实体新增事件(操作前)”事件，触发“P0-自定义事件监听验证”微流程执行");
            if(customMicroFlowAppService == null) {
                throw new BusinessException("自定义微流程还未开发，请联系开发人员！");
            }
            customMicroFlowAppService.p0CustomEventProbe(SingleRequest.from(aeProbeEntitycomseeyonudccommoneventBeforeCreateEvent));
            log.info("成功执行微流程：P0-自定义事件监听验证");
    }


}

