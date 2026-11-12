/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.security.authentication;

import java.io.Serializable;
import java.security.Principal;

public interface Authentication
extends Principal,
Serializable {
    public Object getCredentials();

    public Object getDetails();

    public Object getPrincipal();
}

