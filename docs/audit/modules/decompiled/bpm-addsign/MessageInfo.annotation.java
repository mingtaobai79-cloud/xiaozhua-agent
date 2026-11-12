/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.OpenApi
 */
package com.seeyon.boot.annotation;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.OpenApi;
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(value={ElementType.TYPE})
@Retention(value=RetentionPolicy.RUNTIME)
@Documented
@Inherited
public @interface MessageInfo {
    public String value();

    public String description() default "";

    public String topic();

    public int sort() default 0x7FFFFFFF;

    public OpenApi openApi() default @OpenApi(isOpenApi=false);

    public Custom[] customs() default {};
}
