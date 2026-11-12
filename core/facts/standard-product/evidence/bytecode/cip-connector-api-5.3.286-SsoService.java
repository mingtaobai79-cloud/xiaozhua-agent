/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.cip.connector.api.sso;

import com.seeyon.cip.connector.annotation.CipConnectorComment;
import com.seeyon.cip.connector.enums.SsoClientTypeEnum;
import java.util.Map;

public interface SsoService {
    @CipConnectorComment(value="\u83b7\u53d6\u540d\u79f0")
    public String getName();

    @CipConnectorComment(value="\u83b7\u53d6\u63cf\u8ff0")
    public String getTypeCaption();

    @CipConnectorComment(value="\u767b\u5f55url : \u767b\u5f55urljson : \u767b\u5f55\u4fe1\u606fjson\u4e32userMap : \u7528\u6237\u4fe1\u606fmapclientType :\u5ba2\u6237\u7aef\u7c7b\u578bextendParams : \u6269\u5c55\u5b57\u6bb5")
    public String login(String var1, String var2, Map<String, Object> var3, SsoClientTypeEnum var4, Map<String, Object> var5);

    @CipConnectorComment(value="jsr303\u6821\u9a8c")
    public void check(String var1);

    @CipConnectorComment(value="\u83b7\u53d6\u9875\u9762json\u8bed\u53e5")
    public String getPageJson();

    @CipConnectorComment(value="\u6392\u5e8f")
    public Integer getSortNo();

    @CipConnectorComment(value="\u662f\u5426\u9700\u8981\u7528\u6237\u7ed1\u5b9a\u64cd\u4f5c")
    public boolean needUserBind();
}

