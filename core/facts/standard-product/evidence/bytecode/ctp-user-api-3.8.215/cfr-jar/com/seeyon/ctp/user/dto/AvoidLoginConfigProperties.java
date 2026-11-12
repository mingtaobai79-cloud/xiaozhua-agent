/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.dto;

public class AvoidLoginConfigProperties {
    private String authType;
    private String callbackUrl;
    private String aesKey;
    private String clientId = "v8sso";
    private String clientSecret;
    private String tokenUrl;
    private String authorizeUrl;
    private Boolean isEncrypt = false;

    public String getAuthType() {
        return this.authType;
    }

    public String getCallbackUrl() {
        return this.callbackUrl;
    }

    public String getAesKey() {
        return this.aesKey;
    }

    public String getClientId() {
        return this.clientId;
    }

    public String getClientSecret() {
        return this.clientSecret;
    }

    public String getTokenUrl() {
        return this.tokenUrl;
    }

    public String getAuthorizeUrl() {
        return this.authorizeUrl;
    }

    public Boolean getIsEncrypt() {
        return this.isEncrypt;
    }

    public void setAuthType(String authType) {
        this.authType = authType;
    }

    public void setCallbackUrl(String callbackUrl) {
        this.callbackUrl = callbackUrl;
    }

    public void setAesKey(String aesKey) {
        this.aesKey = aesKey;
    }

    public void setClientId(String clientId) {
        this.clientId = clientId;
    }

    public void setClientSecret(String clientSecret) {
        this.clientSecret = clientSecret;
    }

    public void setTokenUrl(String tokenUrl) {
        this.tokenUrl = tokenUrl;
    }

    public void setAuthorizeUrl(String authorizeUrl) {
        this.authorizeUrl = authorizeUrl;
    }

    public void setIsEncrypt(Boolean isEncrypt) {
        this.isEncrypt = isEncrypt;
    }

    public String toString() {
        return "AvoidLoginConfigProperties(authType=" + this.getAuthType() + ", callbackUrl=" + this.getCallbackUrl() + ", aesKey=" + this.getAesKey() + ", clientId=" + this.getClientId() + ", clientSecret=" + this.getClientSecret() + ", tokenUrl=" + this.getTokenUrl() + ", authorizeUrl=" + this.getAuthorizeUrl() + ", isEncrypt=" + this.getIsEncrypt() + ")";
    }
}

