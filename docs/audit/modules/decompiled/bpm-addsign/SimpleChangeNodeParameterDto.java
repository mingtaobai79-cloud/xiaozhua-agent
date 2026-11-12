/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.BaseDto
 *  com.seeyon.bpm.enums.FlowTypeEnum
 *  com.seeyon.bpm.enums.ProcessExecuteEnum
 *  com.seeyon.bpm.enums.SubProcessExecuteModeEnum
 *  javax.validation.constraints.NotEmpty
 */
package com.seeyon.bpm.dto;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.BaseDto;
import com.seeyon.bpm.dto.AddNodePerson;
import com.seeyon.bpm.enums.FlowTypeEnum;
import com.seeyon.bpm.enums.ProcessExecuteEnum;
import com.seeyon.bpm.enums.SubProcessExecuteModeEnum;
import java.util.List;
import javax.validation.constraints.NotEmpty;

@DtoInfo(value="\u52a0\u7b7e/\u4f1a\u7b7e\u5177\u4f53\u53c2\u6570")
public class SimpleChangeNodeParameterDto
extends BaseDto {
    @NotEmpty
    @DtoAttribute(value="\u52a0\u7b7e\u5177\u4f53\u7684\u4eba\u5458\u5217\u8868", example="")
    private List<AddNodePerson> addNodePersons;
    @DtoAttribute(value="\u52a0\u7b7e\u6a21\u5f0f,\u6b64\u5904\u4ec5\u53ef\u4f7f\u7528 SERIAL\uff1a\u52a0\u7b7e\u5230\u8282\u70b9\u540e\uff1bFRONT\uff1a\u52a0\u7b7e\u5230\u8282\u70b9\u524d\uff1bCURRENT_BRANCH\uff1a\u52a0\u7b7e\u5230\u65c1\u652f\uff1bCURRENT_PARALLEL\uff1a\u4e0e\u5f53\u524d\u8282\u70b9\u5e76\u53d1", example="")
    private FlowTypeEnum flowTypeEnum;
    @DtoAttribute(value="\u6267\u884c\u6a21\u5f0f \u5168\u4f53\u5e76\u53d1 \u7ade\u4e89", example="ALL_PARALLEL")
    private ProcessExecuteEnum processExecuteEnum;
    @DtoAttribute(value="\u591a\u4e2a\u8282\u70b9\u6267\u884c\u6a21\u5f0f  \u4e32\u53d1 \u5e76\u53d1", example="SERIAL")
    private SubProcessExecuteModeEnum nodeExecuteEnum;
    @DtoAttribute(value="\u662f\u5426\u53ea\u8bfb:true\u53ea\u8bfb,false\u7f16\u8f91", example="false")
    private Boolean readOnly = false;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650ID", example="")
    private String policyId;
    @DtoAttribute(value="\u8282\u70b9\u6743\u9650\u540d\u79f0", example="")
    private String policyName;
    @DtoAttribute(value="\u8868\u5355\u6743\u9650ID", example="")
    private String formOperationId;

    public List<AddNodePerson> getAddNodePersons() {
        return this.addNodePersons;
    }

    public FlowTypeEnum getFlowTypeEnum() {
        return this.flowTypeEnum;
    }

    public ProcessExecuteEnum getProcessExecuteEnum() {
        return this.processExecuteEnum;
    }

    public SubProcessExecuteModeEnum getNodeExecuteEnum() {
        return this.nodeExecuteEnum;
    }

    public Boolean getReadOnly() {
        return this.readOnly;
    }

    public String getPolicyId() {
        return this.policyId;
    }

    public String getPolicyName() {
        return this.policyName;
    }

    public String getFormOperationId() {
        return this.formOperationId;
    }

    public void setAddNodePersons(List<AddNodePerson> addNodePersons) {
        this.addNodePersons = addNodePersons;
    }

    public void setFlowTypeEnum(FlowTypeEnum flowTypeEnum) {
        this.flowTypeEnum = flowTypeEnum;
    }

    public void setProcessExecuteEnum(ProcessExecuteEnum processExecuteEnum) {
        this.processExecuteEnum = processExecuteEnum;
    }

    public void setNodeExecuteEnum(SubProcessExecuteModeEnum nodeExecuteEnum) {
        this.nodeExecuteEnum = nodeExecuteEnum;
    }

    public void setReadOnly(Boolean readOnly) {
        this.readOnly = readOnly;
    }

    public void setPolicyId(String policyId) {
        this.policyId = policyId;
    }

    public void setPolicyName(String policyName) {
        this.policyName = policyName;
    }

    public void setFormOperationId(String formOperationId) {
        this.formOperationId = formOperationId;
    }
}
