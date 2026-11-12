/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.CommandDto
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.dto.ChangeNodeRequestDto
 *  com.seeyon.bpm.dto.PreMatchRequestDto
 *  com.seeyon.bpm.dto.TrackRequestDto
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto.approval;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.CommandDto;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.dto.ChangeNodeRequestDto;
import com.seeyon.bpm.dto.PreMatchRequestDto;
import com.seeyon.bpm.dto.TrackRequestDto;
import java.util.List;
import java.util.Map;
import javax.validation.constraints.NotNull;

@DtoInfo(value="审批发送dto")
public class BpmSendUdcDto
extends CommandDto {
    @DtoAttribute(value="模板id", example="")
    private Long templateId;
    @DtoAttribute(value="跟实体id", example="")
    private Long rootEntityId;
    @DtoAttribute(value="跟实体名称", example="com.seeyon.dynamic7207120140245815188.v2_0_0.domain.entity.Entity09942142")
    private String rootEntityName;
    @DtoAttribute(value="流程实例ID")
    private Long caseId;
    @DtoAttribute(value="当前用户ID", example="1")
    @NotNull(message="userId不能空")
    private @NotNull(message="userId不能空") Long userId;
    @DtoAttribute(value="发起人附言")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="预提交分支匹配结果")
    private PreMatchRequestDto preMatchRequestDto;
    @DtoAttribute(value="根据表单定义传入表单数据的json字符串。key为实体设置页面的字段名称；字段类型为选人,value为人员id；字段类型为枚举,value为枚举的id;字段类型为日期:value为时间戳。重复表的key:重复表实体名称+DtoList. actionType:NORMAL-无变化，INSERT-新增，DELETE-删除，UPDATE-修改", example="{\"xingming\":\"483551494461775872\",\"nianling\":11,\"zhekou\":221,\"beizhu\":\"222\",\"shifoujiekouliucheng\":\"506786870718589952\",\"chushengriqi\":\"1627625028742\",\"shangbanshijian\":\"1627488427993\",\"ruzhiriqishijian\":\"1627488007492\",\"kaiguan\":true,\"shunfengcc72806mingxiDtoList\":[{\"actionType\":\"INSERT\",\"xingming\":\"483551494461775872\"},{\"actionType\":\"INSERT\",\"xingming\":\"490818238549230592\"}]}")
    private Map<String, Object> formData;
    @DtoAttribute(value="表单数据ID", example="1")
    @NotNull(message="表单记录id不能为空")
    private @NotNull(message="表单记录id不能为空") Long formRecordId;
    @DtoAttribute(value="表单应用名称", example="dynamic8113236162288896776")
    private String applicationName;
    @DtoAttribute(value="udc表单url")
    private String startFormUrl;
    @DtoAttribute(value="加签相关请求参数，没有做加签相关操作，传递NULL就可以", example="")
    private List<ChangeNodeRequestDto> changeNodeRequestDtos;
    @DtoAttribute(value="知会选人组件返回的信息", example="[123,456]")
    private String informAddSelectPeoples;
    @DtoAttribute(value="是否必填", example="true")
    private boolean commentRequired = false;
    @DtoAttribute(value="事项id", example="20712014024581518")
    private Long affairId;
    @DtoAttribute(value="流程跟踪参数")
    private TrackRequestDto trackRequestDto;

    public String toString() {
        StringBuilder sb = new StringBuilder("{");
        if (this.templateId != null) {
            sb.append("\"templateId\":").append(this.templateId).append(",");
        }
        if (this.rootEntityId != null) {
            sb.append("\"rootEntityId\":").append(this.rootEntityId).append(",");
        }
        if (this.rootEntityName != null) {
            sb.append("\"rootEntityName\":\"").append(this.rootEntityName).append("\",");
        }
        if (this.caseId != null) {
            sb.append("\"caseId\":").append(this.caseId).append(",");
        }
        if (this.userId != null) {
            sb.append("\"userId\":").append(this.userId).append(",");
        }
        if (this.formRecordId != null) {
            sb.append("\"formRecordId\":").append(this.formRecordId).append(",");
        }
        if (this.applicationName != null) {
            sb.append("\"applicationName\":\"").append(this.applicationName).append("\",");
        }
        if (this.startFormUrl != null) {
            sb.append("\"startFormUrl\":\"").append(this.startFormUrl).append("\"}");
        }
        if (this.affairId != null) {
            sb.append("\"affairId\":\"").append(this.affairId).append("\"}");
        }
        return sb.toString();
    }

    public Long getTemplateId() {
        return this.templateId;
    }

    public Long getRootEntityId() {
        return this.rootEntityId;
    }

    public String getRootEntityName() {
        return this.rootEntityName;
    }

    public Long getCaseId() {
        return this.caseId;
    }

    public Long getUserId() {
        return this.userId;
    }

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public PreMatchRequestDto getPreMatchRequestDto() {
        return this.preMatchRequestDto;
    }

    public Map<String, Object> getFormData() {
        return this.formData;
    }

    public Long getFormRecordId() {
        return this.formRecordId;
    }

    public String getApplicationName() {
        return this.applicationName;
    }

    public String getStartFormUrl() {
        return this.startFormUrl;
    }

    public List<ChangeNodeRequestDto> getChangeNodeRequestDtos() {
        return this.changeNodeRequestDtos;
    }

    public String getInformAddSelectPeoples() {
        return this.informAddSelectPeoples;
    }

    public boolean isCommentRequired() {
        return this.commentRequired;
    }

    public Long getAffairId() {
        return this.affairId;
    }

    public TrackRequestDto getTrackRequestDto() {
        return this.trackRequestDto;
    }

    public void setTemplateId(Long templateId) {
        this.templateId = templateId;
    }

    public void setRootEntityId(Long rootEntityId) {
        this.rootEntityId = rootEntityId;
    }

    public void setRootEntityName(String rootEntityName) {
        this.rootEntityName = rootEntityName;
    }

    public void setCaseId(Long caseId) {
        this.caseId = caseId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }

    public void setPreMatchRequestDto(PreMatchRequestDto preMatchRequestDto) {
        this.preMatchRequestDto = preMatchRequestDto;
    }

    public void setFormData(Map<String, Object> formData) {
        this.formData = formData;
    }

    public void setFormRecordId(Long formRecordId) {
        this.formRecordId = formRecordId;
    }

    public void setApplicationName(String applicationName) {
        this.applicationName = applicationName;
    }

    public void setStartFormUrl(String startFormUrl) {
        this.startFormUrl = startFormUrl;
    }

    public void setChangeNodeRequestDtos(List<ChangeNodeRequestDto> changeNodeRequestDtos) {
        this.changeNodeRequestDtos = changeNodeRequestDtos;
    }

    public void setInformAddSelectPeoples(String informAddSelectPeoples) {
        this.informAddSelectPeoples = informAddSelectPeoples;
    }

    public void setCommentRequired(boolean commentRequired) {
        this.commentRequired = commentRequired;
    }

    public void setAffairId(Long affairId) {
        this.affairId = affairId;
    }

    public void setTrackRequestDto(TrackRequestDto trackRequestDto) {
        this.trackRequestDto = trackRequestDto;
    }
}
