package com.seeyon.datamigration163126498398523384.schedule;

import com.seeyon.datamigration163126498398523384.api.microflow.CustomMicroFlowAppService;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.starter.schedule.annotation.CtpSchedule;
import com.seeyon.boot.starter.schedule.api.SeeyonJob;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
/**
 * P0-自定义定时验证
 * @author seeyon
 * @date 2026-11-21 04:07:19
 * @since 1.0.0
*/
@Slf4j
@CtpSchedule(jobName = "PcSpL2lTP5Xq1FGj", description = "P0-自定义定时验证")
public class P0CustomScheduleProbeSchedule implements SeeyonJob {

    @Autowired(required = false)
    private CustomMicroFlowAppService customMicroFlowAppService;

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public SingleResponse<?> exec() {
        com.seeyon.boot.starter.udcrt.util.MicroFlowRuntimeUtil.saveDefaultValue4RequestContext();
        log.info("jobClass:[P0CustomScheduleProbeSchedule] jobName:[PcSpL2lTP5Xq1FGj] start! ");
        if(customMicroFlowAppService == null) {
            throw new BusinessException("自定义微流程还未开发，请联系开发人员！");
        }
        customMicroFlowAppService.p0CustomScheduleProbe();
        return SingleResponse.ok();
    }
}