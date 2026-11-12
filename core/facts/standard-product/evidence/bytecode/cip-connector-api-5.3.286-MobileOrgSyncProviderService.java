/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.cip.connector.api.mobile;

import com.seeyon.cip.connector.annotation.CipConnectorComment;
import com.seeyon.cip.connector.api.mobile.MobileProviderService;
import com.seeyon.cip.connector.dto.mobile.MobileOrgDto;
import com.seeyon.cip.connector.dto.mobile.MobilePlatformConfigDto;
import com.seeyon.cip.connector.dto.mobile.MobileUnitRequestDto;
import com.seeyon.cip.connector.dto.mobile.MobileUserRequestDto;
import com.seeyon.cip.connector.dto.mobile.MobileUserResponseDto;

public interface MobileOrgSyncProviderService
extends MobileProviderService {
    @CipConnectorComment(value="\u7ec4\u7ec7\u540c\u6b65dto : \u540c\u6b65\u7ec4\u7ec7\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public Long syncUnit(MobileUnitRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u66f4\u65b0\u7ec4\u7ec7dto : \u540c\u6b65\u7ec4\u7ec7\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public void updateUnit(MobileUnitRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u67e5\u8be2\u7ec4\u7ec7dto : \u540c\u6b65\u7ec4\u7ec7\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public String getUnit(MobileUnitRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u5220\u9664\u7ec4\u7ec7dto : \u540c\u6b65\u7ec4\u7ec7\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public void removeUnit(MobileUnitRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u4eba\u5458\u540c\u6b65dto : \u540c\u6b65\u7528\u6237\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public String syncUser(MobileUserRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u66f4\u65b0\u4eba\u5458dto : \u540c\u6b65\u7528\u6237\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public String updateUser(MobileUserRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u67e5\u8be2\u4eba\u5458dto : \u540c\u6b65\u7528\u6237\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public MobileUserResponseDto getUser(MobileUserRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u5220\u9664\u4eba\u5458dto : \u540c\u6b65\u7528\u6237\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    public MobileUserResponseDto removeUser(MobileUserRequestDto var1, MobilePlatformConfigDto var2);

    @CipConnectorComment(value="\u7ec4\u7ec7\u540c\u6b65 \u8fd4\u56dedtodto : \u540c\u6b65\u7ec4\u7ec7\u4fe1\u606fdtoconfigDto : \u914d\u7f6e\u4fe1\u606f")
    default public MobileOrgDto syncUnitNew(MobileUnitRequestDto dto, MobilePlatformConfigDto configDto) {
        return null;
    }
}

