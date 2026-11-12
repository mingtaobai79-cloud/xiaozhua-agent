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

@DtoInfo(value="\u5ba1\u6279\u53d1\u9001dto")
public class BpmSendUdcDto
extends CommandDto {
    @DtoAttribute(value="\u6a21\u677fid", example="")
    private Long templateId;
    @DtoAttribute(value="\u8ddf\u5b9e\u4f53id", example="")
    private Long rootEntityId;
    @DtoAttribute(value="\u8ddf\u5b9e\u4f53\u540d\u79f0", example="com.seeyon.dynamic7207120140245815188.v2_0_0.domain.entity.Entity09942142")
    private String rootEntityName;
    @DtoAttribute(value="\u6d41\u7a0b\u5b9e\u4f8bID")
    private Long caseId;
    @DtoAttribute(value="\u5f53\u524d\u7528\u6237ID", example="1")
    @NotNull(message="userId\u4e0d\u80fd\u7a7a")
    private @NotNull(message="userId\u4e0d\u80fd\u7a7a") Long userId;
    @DtoAttribute(value="\u53d1\u8d77\u4eba\u9644\u8a00")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="\u9884\u63d0\u4ea4\u5206\u652f\u5339\u914d\u7ed3\u679c")
    private PreMatchRequestDto preMatchRequestDto;
    @DtoAttribute(value="\u6839\u636e\u8868\u5355\u5b9a\u4e49\u4f20\u5165\u8868\u5355\u6570\u636e\u7684json\u5b57\u7b26\u4e32\u3002key\u4e3a\u5b9e\u4f53\u8bbe\u7f6e\u9875\u9762\u7684\u5b57\u6bb5\u540d\u79f0\uff1b\u5b57\u6bb5\u7c7b\u578b\u4e3a\u9009\u4eba,value\u4e3a\u4eba\u5458id\uff1b\u5b57\u6bb5\u7c7b\u578b\u4e3a\u679a\u4e3e,value\u4e3a\u679a\u4e3e\u7684id;\u5b57\u6bb5\u7c7b\u578b\u4e3a\u65e5\u671f:value\u4e3a\u65f6\u95f4\u6233\u3002\u91cd\u590d\u8868\u7684key:\u91cd\u590d\u8868\u5b9e\u4f53\u540d\u79f0+DtoList. actionType:NORMAL-\u65e0\u53d8\u5316\uff0cINSERT-\u65b0\u589e\uff0cDELETE-\u5220\u9664\uff0cUPDATE-\u4fee\u6539", example="{\"xingming\":\"483551494461775872\",\"nianling\":11,\"zhekou\":221,\"beizhu\":\"222\",\"shifoujiekouliucheng\":\"506786870718589952\",\"chushengriqi\":\"1627625028742\",\"shangbanshijian\":\"1627488427993\",\"ruzhiriqishijian\":\"1627488007492\",\"kaiguan\":true,\"shunfengcc72806mingxiDtoList\":[{\"actionType\":\"INSERT\",\"xingming\":\"483551494461775872\"},{\"actionType\":\"INSERT\",\"xingming\":\"490818238549230592\"}]}")
    private Map<String, Object> formData;
    @DtoAttribute(value="\u8868\u5355\u6570\u636eID", example="1")
    @NotNull(message="\u8868\u5355\u8bb0\u5f55id\u4e0d\u80fd\u4e3a\u7a7a")
    private @NotNull(message="\u8868\u5355\u8bb0\u5f55id\u4e0d\u80fd\u4e3a\u7a7a") Long formRecordId;
    @DtoAttribute(value="\u8868\u5355\u5e94\u7528\u540d\u79f0", example="dynamic8113236162288896776")
    private String applicationName;
    @DtoAttribute(value="udc\u8868\u5355url")
    private String startFormUrl;
    @DtoAttribute(value="\u52a0\u7b7e\u76f8\u5173\u8bf7\u6c42\u53c2\u6570\uff0c\u6ca1\u6709\u505a\u52a0\u7b7e\u76f8\u5173\u64cd\u4f5c\uff0c\u4f20\u9012NULL\u5c31\u53ef\u4ee5", example="")
    private List<ChangeNodeRequestDto> changeNodeRequestDtos;
    @DtoAttribute(value="\u77e5\u4f1a\u9009\u4eba\u7ec4\u4ef6\u8fd4\u56de\u7684\u4fe1\u606f", example="[123,456]")
    private String informAddSelectPeoples;
    @DtoAttribute(value="\u662f\u5426\u5fc5\u586b", example="true")
    private boolean commentRequired = false;
    @DtoAttribute(value="\u4e8b\u9879id", example="20712014024581518")
    private Long affairId;
    @DtoAttribute(value="\u6d41\u7a0b\u8ddf\u8e2a\u53c2\u6570")
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
