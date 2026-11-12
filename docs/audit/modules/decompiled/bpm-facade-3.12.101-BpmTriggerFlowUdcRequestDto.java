/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.DtoAttribute
 *  com.seeyon.boot.annotation.DtoInfo
 *  com.seeyon.boot.transport.CommandDto
 *  com.seeyon.bpm.dto.BpmCommentDto
 *  com.seeyon.bpm.enums.PageTypeEnum
 *  javax.validation.constraints.NotNull
 */
package com.seeyon.bpm.dto.approval;

import com.seeyon.boot.annotation.DtoAttribute;
import com.seeyon.boot.annotation.DtoInfo;
import com.seeyon.boot.transport.CommandDto;
import com.seeyon.bpm.dto.BpmCommentDto;
import com.seeyon.bpm.enums.PageTypeEnum;
import java.util.Map;
import javax.validation.constraints.NotNull;

@DtoInfo(value="udc\u4fdd\u5b58\u8349\u7a3f\u5e76\u4e14\u751f\u6210\u5f85\u529edto")
public class BpmTriggerFlowUdcRequestDto
extends CommandDto {
    private static final long serialVersionUID = -5883293787371399180L;
    @DtoAttribute(value="\u6a21\u677fid", example="")
    private Long templateId;
    @DtoAttribute(value="\u8ddf\u5b9e\u4f53id", example="")
    private Long rootEntityId;
    @DtoAttribute(value="\u8ddf\u5b9e\u4f53\u540d\u79f0", example="com.seeyon.dynamic7207120140245815188.v2_0_0.domain.entity.Entity09942142")
    private String rootEntityName;
    @DtoAttribute(value="\u5f53\u524d\u7528\u6237ID", example="1")
    @NotNull(message="userId\u4e0d\u80fd\u7a7a")
    private @NotNull(message="userId\u4e0d\u80fd\u7a7a") Long userId;
    @DtoAttribute(value="\u53d1\u8d77\u4eba\u9644\u8a00")
    private BpmCommentDto commentDto;
    @DtoAttribute(value="\u6839\u636e\u8868\u5355\u5b9a\u4e49\u4f20\u5165\u8868\u5355\u6570\u636e\u7684json\u5b57\u7b26\u4e32\u3002key\u4e3a\u5b9e\u4f53\u8bbe\u7f6e\u9875\u9762\u7684\u5b57\u6bb5\u540d\u79f0\uff1b\u5b57\u6bb5\u7c7b\u578b\u4e3a\u9009\u4eba,value\u4e3a\u4eba\u5458id\uff1b\u5b57\u6bb5\u7c7b\u578b\u4e3a\u679a\u4e3e,value\u4e3a\u679a\u4e3e\u7684id;\u5b57\u6bb5\u7c7b\u578b\u4e3a\u65e5\u671f:value\u4e3a\u65f6\u95f4\u6233\u3002\u91cd\u590d\u8868\u7684key:\u91cd\u590d\u8868\u5b9e\u4f53\u540d\u79f0+DtoList. actionType:NORMAL-\u65e0\u53d8\u5316\uff0cINSERT-\u65b0\u589e\uff0cDELETE-\u5220\u9664\uff0cUPDATE-\u4fee\u6539", example="{\"xingming\":\"483551494461775872\",\"nianling\":11,\"zhekou\":221,\"beizhu\":\"222\",\"shifoujiekouliucheng\":\"506786870718589952\",\"chushengriqi\":\"1627625028742\",\"shangbanshijian\":\"1627488427993\",\"ruzhiriqishijian\":\"1627488007492\",\"kaiguan\":true,\"shunfengcc72806mingxiDtoList\":[{\"actionType\":\"INSERT\",\"xingming\":\"483551494461775872\"},{\"actionType\":\"INSERT\",\"xingming\":\"490818238549230592\"}]}")
    private Map<String, Object> formData;
    @DtoAttribute(value="\u8868\u5355\u6570\u636eID", example="1")
    @NotNull(message="\u8868\u5355\u8bb0\u5f55id\u4e0d\u80fd\u4e3a\u7a7a")
    private @NotNull(message="\u8868\u5355\u8bb0\u5f55id\u4e0d\u80fd\u4e3a\u7a7a") Long formRecordId;
    @DtoAttribute(value="\u6a21\u677fguid,\u4e00\u4e2a\u6a21\u677f\u552f\u4e00", example="")
    private Long templateGuid;
    @DtoAttribute(value="\u9875\u9762\u5730\u5740", example="")
    private String pageUrl;
    @DtoAttribute(value="\u9875\u9762\u7c7b\u578b", example="")
    private PageTypeEnum pageType;
    @DtoAttribute(value="\u9875\u9762guid", example="")
    private Long pageGuid;
    @DtoAttribute(value="\u662f\u5426\u9700\u8981\u53d1\u8d77\u6d41\u7a0b", example="")
    private Boolean needSend;
    @DtoAttribute(value="\u6a21\u677f\u9875\u9762\u53c2\u6570", example="xxx")
    private String pageParameter;

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
        if (this.userId != null) {
            sb.append("\"userId\":").append(this.userId).append(",");
        }
        if (this.formRecordId != null) {
            sb.append("\"formRecordId\":").append(this.formRecordId).append(",");
        }
        if (this.templateGuid != null) {
            sb.append("\"templateGuid\":").append(this.templateGuid).append(",");
        }
        if (this.pageUrl != null) {
            sb.append("\"pageUrl\":\"").append(this.pageUrl).append("\",");
        }
        if (this.pageType != null) {
            sb.append("\"pageType\":").append(this.pageType).append(",");
        }
        if (this.pageGuid != null) {
            sb.append("\"pageGuid\":").append(this.pageGuid).append(",");
        }
        if (this.needSend != null) {
            sb.append("\"needSend\":").append(this.needSend).append("}");
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

    public Long getUserId() {
        return this.userId;
    }

    public BpmCommentDto getCommentDto() {
        return this.commentDto;
    }

    public Map<String, Object> getFormData() {
        return this.formData;
    }

    public Long getFormRecordId() {
        return this.formRecordId;
    }

    public Long getTemplateGuid() {
        return this.templateGuid;
    }

    public String getPageUrl() {
        return this.pageUrl;
    }

    public PageTypeEnum getPageType() {
        return this.pageType;
    }

    public Long getPageGuid() {
        return this.pageGuid;
    }

    public Boolean getNeedSend() {
        return this.needSend;
    }

    public String getPageParameter() {
        return this.pageParameter;
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

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setCommentDto(BpmCommentDto commentDto) {
        this.commentDto = commentDto;
    }

    public void setFormData(Map<String, Object> formData) {
        this.formData = formData;
    }

    public void setFormRecordId(Long formRecordId) {
        this.formRecordId = formRecordId;
    }

    public void setTemplateGuid(Long templateGuid) {
        this.templateGuid = templateGuid;
    }

    public void setPageUrl(String pageUrl) {
        this.pageUrl = pageUrl;
    }

    public void setPageType(PageTypeEnum pageType) {
        this.pageType = pageType;
    }

    public void setPageGuid(Long pageGuid) {
        this.pageGuid = pageGuid;
    }

    public void setNeedSend(Boolean needSend) {
        this.needSend = needSend;
    }

    public void setPageParameter(String pageParameter) {
        this.pageParameter = pageParameter;
    }
}
