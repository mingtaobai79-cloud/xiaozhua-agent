/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.EntityInfo
 *  com.seeyon.boot.domain.entity.BaseEntity
 *  com.seeyon.boot.domain.entity.BaseSignEntityable
 *  javax.persistence.Column
 *  javax.persistence.Entity
 *  javax.persistence.Table
 *  javax.persistence.Transient
 *  org.apache.ibatis.type.Alias
 */
package com.seeyon.boot.starter.web.domain.entity;

import com.seeyon.boot.annotation.EntityInfo;
import com.seeyon.boot.domain.entity.BaseEntity;
import com.seeyon.boot.domain.entity.BaseSignEntityable;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Table;
import javax.persistence.Transient;
import org.apache.ibatis.type.Alias;

@Entity
@Table(name="access_audit_log")
@EntityInfo(value="审计日志记录表记录表")
@Alias(value="AccessAuditLog")
public class AccessAuditLg
extends BaseEntity
implements BaseSignEntityable {
    @Column(name="log_type", columnDefinition="varchar(50) NOT NULL DEFAULT '' COMMENT '日志类型'")
    private String logType = "";
    @Column(name="log_biz_type", columnDefinition="varchar(50) NOT NULL DEFAULT '' COMMENT '日志业务类型'")
    private String logBizType = "";
    @Column(name="user_id", columnDefinition="BIGINT(20) NOT NULL DEFAULT -1 COMMENT '用户id'")
    private Long userId = -1L;
    @Column(name="org_id", columnDefinition="BIGINT(20) NOT NULL DEFAULT -1 COMMENT '组织id'")
    private Long orgId = -1L;
    @Column(name="op_time", columnDefinition="varchar(50) NOT NULL DEFAULT '' COMMENT '操作时间'")
    private String opTime = "";
    @Column(name="ip", columnDefinition="varchar(50) NOT NULL DEFAULT '' COMMENT '操作ip'")
    private String ip = "";
    @Column(name="app_id", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '操作应用'")
    private String appId = "";
    @Column(name="op_type", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '操作类型'")
    private String opType = "";
    @Column(name="category", columnDefinition="varchar(4000) NOT NULL DEFAULT '' COMMENT '操作对象'")
    private String category = "";
    @Column(name="description", columnDefinition="varchar(4000) NOT NULL DEFAULT '' COMMENT '操作描述'")
    private String description = "";
    @Column(name="trace_id", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '链路id'")
    private String traceId = "";
    @Column(name="param5", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段5'")
    private String param5;
    @Column(name="param6", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段6'")
    private String param6;
    @Column(name="param7", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段7'")
    private String param7;
    @Column(name="param8", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段8'")
    private String param8;
    @Column(name="param9", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段9'")
    private String param9;
    @Column(name="param10", columnDefinition="varchar(250) NOT NULL DEFAULT '' COMMENT '扩展字段10'")
    private String param10;
    @Column(name="data_Sign", nullable=false, columnDefinition="VARCHAR(255) COMMENT '加签数据'")
    private String dataSign = "";
    @Transient
    private Integer dataSignSuccess;

    public void setDataSign(String dataSign) {
        this.dataSign = dataSign;
    }

    public void setDataSignSuccess(Integer dataSignSuccess) {
        this.dataSignSuccess = dataSignSuccess;
    }

    public String getDataSign() {
        return this.dataSign;
    }

    public Integer getDataSignSuccess() {
        return this.dataSignSuccess;
    }

    public String getLogType() {
        return this.logType;
    }

    public String getLogBizType() {
        return this.logBizType;
    }

    public Long getUserId() {
        return this.userId;
    }

    public Long getOrgId() {
        return this.orgId;
    }

    public String getOpTime() {
        return this.opTime;
    }

    public String getIp() {
        return this.ip;
    }

    public String getAppId() {
        return this.appId;
    }

    public String getOpType() {
        return this.opType;
    }

    public String getCategory() {
        return this.category;
    }

    public String getDescription() {
        return this.description;
    }

    public String getTraceId() {
        return this.traceId;
    }

    public String getParam5() {
        return this.param5;
    }

    public String getParam6() {
        return this.param6;
    }

    public String getParam7() {
        return this.param7;
    }

    public String getParam8() {
        return this.param8;
    }

    public String getParam9() {
        return this.param9;
    }

    public String getParam10() {
        return this.param10;
    }

    public void setLogType(String logType) {
        this.logType = logType;
    }

    public void setLogBizType(String logBizType) {
        this.logBizType = logBizType;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setOrgId(Long orgId) {
        this.orgId = orgId;
    }

    public void setOpTime(String opTime) {
        this.opTime = opTime;
    }

    public void setIp(String ip) {
        this.ip = ip;
    }

    public void setAppId(String appId) {
        this.appId = appId;
    }

    public void setOpType(String opType) {
        this.opType = opType;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setTraceId(String traceId) {
        this.traceId = traceId;
    }

    public void setParam5(String param5) {
        this.param5 = param5;
    }

    public void setParam6(String param6) {
        this.param6 = param6;
    }

    public void setParam7(String param7) {
        this.param7 = param7;
    }

    public void setParam8(String param8) {
        this.param8 = param8;
    }

    public void setParam9(String param9) {
        this.param9 = param9;
    }

    public void setParam10(String param10) {
        this.param10 = param10;
    }
}
