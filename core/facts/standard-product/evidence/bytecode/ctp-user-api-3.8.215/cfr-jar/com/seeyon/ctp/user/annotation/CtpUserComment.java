/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.stereotype.Indexed
 */
package com.seeyon.ctp.user.annotation;

import com.seeyon.ctp.user.annotation.CtpUserComments;
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import org.springframework.stereotype.Indexed;

@Target(value={ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@Retention(value=RetentionPolicy.RUNTIME)
@Documented
@Indexed
@Repeatable(value=CtpUserComments.class)
public @interface CtpUserComment {
    public String value();
}

