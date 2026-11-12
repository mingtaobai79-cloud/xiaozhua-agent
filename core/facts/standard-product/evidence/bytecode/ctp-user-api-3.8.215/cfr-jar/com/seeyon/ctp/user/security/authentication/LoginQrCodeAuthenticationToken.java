/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.security.authentication;

import com.seeyon.ctp.user.security.authentication.AbstractAuthenticationToken;

public class LoginQrCodeAuthenticationToken
extends AbstractAuthenticationToken {
    private final Object principal;

    public LoginQrCodeAuthenticationToken(Object principal) {
        this.principal = principal;
    }

    @Override
    public Object getCredentials() {
        return null;
    }

    @Override
    public Object getPrincipal() {
        return this.principal;
    }
}

