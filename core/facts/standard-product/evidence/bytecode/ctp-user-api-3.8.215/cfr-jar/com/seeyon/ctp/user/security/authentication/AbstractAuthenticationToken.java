/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.security.authentication;

import com.seeyon.ctp.user.security.authentication.Authentication;

public abstract class AbstractAuthenticationToken
implements Authentication {
    private Object details;

    @Override
    public String getName() {
        return this.getPrincipal() == null ? "" : this.getPrincipal().toString();
    }

    @Override
    public Object getDetails() {
        return this.details;
    }

    public void setDetails(Object details) {
        this.details = details;
    }
}

