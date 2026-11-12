/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmAppInfoDto
 *  com.seeyon.bpm.dto.UpgradeInfoDto
 *  com.seeyon.bpm.dto.transport.BpmExportInitDataDto
 *  com.seeyon.bpm.dto.transport.BpmInitParamDto
 */
package com.seeyon.bpm.api.common;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmAppInfoDto;
import com.seeyon.bpm.dto.UpgradeInfoDto;
import com.seeyon.bpm.dto.transport.BpmExportInitDataDto;
import com.seeyon.bpm.dto.transport.BpmInitParamDto;

public interface BpmDeployAppService {
    public SingleResponse<BpmExportInitDataDto> upgradeBpmTemplateVersion(SingleRequest<String> var1);

    public SingleResponse<BpmExportInitDataDto> deployBpmTemplatesIndependent(SingleRequest<String> var1);

    public SingleResponse<Void> afterFormAppDataInit(SingleRequest<BpmInitParamDto> var1);

    public SingleResponse<String> upgradeCommon(SingleRequest<UpgradeInfoDto> var1);

    public SingleResponse<String> autoDeployStartAndAuth(SingleRequest<BpmAppInfoDto> var1);

    public ListResponse<String> usedFrames(SingleRequest<BpmAppInfoDto> var1);
}
