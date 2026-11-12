/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.dto.SimpleChangeNodeParameterDto
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.SimpleChangeNodeParameterDto;
import javax.validation.constraints.NotNull;

@DtoInfo(value="\u52a0\u7b7e\u51cf\u7b7e")
public class SimpleChangeProcessRequestDto
extends BaseDto {
    @DtoAttribute(value="\u6d41\u7a0bId,processJson\uff0c\u4f18\u5148\u53d6processJson\uff0c\u6ca1\u6709\u5c31\u53d6processId\u5728\u6570\u636e\u5e93\u4e2d\u5bf9\u5e94\u7684\u6d41\u7a0b\u56fe", example="687435655566")
    private Long processId;
    @DtoAttribute(value="\u6d41\u7a0b\u56feJson\uff0c\u548cprocessId\u7ec4\u5408\u4f7f\u7528\uff0c\u4f18\u5148\u53d6baseProcessXml\uff0c\u6ca1\u6709\u5c31\u53d6processId\u5728\u6570\u636e\u5e93\u4e2d\u5bf9\u5e94\u7684\u6d41\u7a0b\u56fe", example="")
    private String processJson;
    @DtoAttribute(value="\u662f\u5426\u4fdd\u5b58\u6d41\u7a0b\u56fe", example="")
    private boolean saveProcess;
    @DtoAttribute(value="\u5f53\u524d\u8282\u70b9ID", example="1234567890")
    @NotNull
    private String currentActivityId;
    @DtoAttribute(value="\u5f53\u524dWorkItem\u7684ID", example="1234567890")
    private String workItemId;
    @DtoAttribute(value="\u662f\u5426\u63d2\u5165\u65e5\u5fd7", example="")
    private boolean needInsertLog = false;
    @DtoAttribute(value="\u52a0\u7b7e/\u4f1a\u7b7e\u5177\u4f53\u53c2\u6570", example="")
    private SimpleChangeNodeParameterDto simpleChangeNodeParameterDto;

    public Long getProcessId() {
        return this.processId;
    }

    public String getProcessJson() {
        return this.processJson;
    }

    public boolean isSaveProcess() {
        return this.saveProcess;
    }

    public String getCurrentActivityId() {
        return this.currentActivityId;
    }

    public String getWorkItemId() {
        return this.workItemId;
    }

    public boolean isNeedInsertLog() {
        return this.needInsertLog;
    }

    public SimpleChangeNodeParameterDto getSimpleChangeNodeParameterDto() {
        return this.simpleChangeNodeParameterDto;
    }

    public void setProcessId(Long processId) {
        this.processId = processId;
    }

    public void setProcessJson(String processJson) {
        this.processJson = processJson;
    }

    public void setSaveProcess(boolean saveProcess) {
        this.saveProcess = saveProcess;
    }

    public void setCurrentActivityId(String currentActivityId) {
        this.currentActivityId = currentActivityId;
    }

    public void setWorkItemId(String workItemId) {
        this.workItemId = workItemId;
    }

    public void setNeedInsertLog(boolean needInsertLog) {
        this.needInsertLog = needInsertLog;
    }

    public void setSimpleChangeNodeParameterDto(SimpleChangeNodeParameterDto simpleChangeNodeParameterDto) {
        this.simpleChangeNodeParameterDto = simpleChangeNodeParameterDto;
    }
}
