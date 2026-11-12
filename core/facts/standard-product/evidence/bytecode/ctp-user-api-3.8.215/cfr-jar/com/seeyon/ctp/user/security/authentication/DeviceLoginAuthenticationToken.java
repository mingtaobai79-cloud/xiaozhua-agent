/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.security.authentication;

import com.seeyon.ctp.user.security.authentication.AbstractAuthenticationToken;

public class DeviceLoginAuthenticationToken
extends AbstractAuthenticationToken {
    private final Object principal;
    private final String credentials;

    public DeviceLoginAuthenticationToken(Object principal, String credentials) {
        this.principal = principal;
        this.credentials = credentials;
    }

    @Override
    public Object getCredentials() {
        return this.credentials;
    }

    @Override
    public Object getPrincipal() {
        return this.principal;
    }
}

