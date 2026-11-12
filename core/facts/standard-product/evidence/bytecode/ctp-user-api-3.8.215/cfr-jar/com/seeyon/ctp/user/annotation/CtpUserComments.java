/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.annotation;

import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(value={ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@Retention(value=RetentionPolicy.RUNTIME)
@Documented
public @interface CtpUserComments {
    public CtpUserComment[] value();
}

