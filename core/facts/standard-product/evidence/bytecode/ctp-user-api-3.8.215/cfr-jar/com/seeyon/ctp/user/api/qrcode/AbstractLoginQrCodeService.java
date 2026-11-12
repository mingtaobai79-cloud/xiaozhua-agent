/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.api.qrcode;

import com.seeyon.ctp.user.dto.CtpLoginQrCodeDto;
import com.seeyon.ctp.user.dto.QrcodeResultDto;

public abstract class AbstractLoginQrCodeService {
    public abstract String getQrCodeAuthenticationType();

    public abstract CtpLoginQrCodeDto generateQrCode();

    public abstract QrcodeResultDto roundScanResult(String var1);
}

