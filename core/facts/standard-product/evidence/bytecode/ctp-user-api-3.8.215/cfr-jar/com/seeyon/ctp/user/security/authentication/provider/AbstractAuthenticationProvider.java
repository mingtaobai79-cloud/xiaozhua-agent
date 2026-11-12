/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.stereotype.Component
 */
package com.seeyon.ctp.user.security.authentication.provider;

import com.seeyon.ctp.user.security.authentication.Authentication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public abstract class AbstractAuthenticationProvider {
    private static final Logger log = LoggerFactory.getLogger(AbstractAuthenticationProvider.class);

    public abstract String getAuthenticationType();

    public abstract boolean supports(Class<?> var1);

    public abstract Authentication retrieveUser(Authentication var1);

    public abstract void preAuthenticationCheck(Authentication var1);

    public abstract void postAuthenticationCheck(Authentication var1);

    public abstract void additionalAuthenticationChecks(Authentication var1);

    public abstract Authentication createSuccessAuthentication(Object var1, Authentication var2);
}

