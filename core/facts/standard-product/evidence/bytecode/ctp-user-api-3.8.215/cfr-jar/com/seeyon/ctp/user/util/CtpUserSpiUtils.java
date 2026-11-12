/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.util.ReflectUtil
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.util.JsonUtils
 *  javax.servlet.http.HttpServletRequest
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.web.context.request.RequestAttributes
 *  org.springframework.web.context.request.RequestContextHolder
 *  org.springframework.web.context.request.ServletRequestAttributes
 */
package com.seeyon.ctp.user.util;

import cn.hutool.core.util.ReflectUtil;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.util.JsonUtils;
import com.seeyon.ctp.user.annotation.CtpUserComment;
import java.lang.reflect.Method;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import javax.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@CtpUserComment(value="spi \u6269\u5c55\u5305\u5de5\u5177\u7c7b\uff0c\u53ef\u4ee5\u83b7\u53d6 bean \u7684\u5b9e\u4f8b\uff0c\u901a\u8fc7\u914d\u7f6e key \u83b7\u53d6 nacos \u6216 yaml \u914d\u7f6e\u5185\u5bb9\u7b49")
public class CtpUserSpiUtils {
    private static final Logger log = LoggerFactory.getLogger(CtpUserSpiUtils.class);
    private static final Map<String, Object> instances = new ConcurrentHashMap<String, Object>();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @CtpUserComment(value="\u83b7\u53d6\u6307\u5b9a\u7c7b\u7684\u5355\u4f8b\u5b9e\u4f8b")
    public static <T> T getInstance(Class<T> clazz) {
        try {
            Object instance = instances.get(clazz.getName());
            if (instance == null) {
                Class<T> clazz2 = clazz;
                synchronized (clazz2) {
                    instance = instances.get(clazz.getName());
                    if (instance == null) {
                        instance = clazz.getDeclaredConstructor(new Class[0]).newInstance(new Object[0]);
                        instances.put(clazz.getName(), instance);
                    }
                }
            }
            return (T)instance;
        }
        catch (Exception e) {
            log.error("getInstance\u5b9e\u4f8b\u5316\u5f02\u5e38\uff1a{}", (Object)e.getMessage(), (Object)e);
            return null;
        }
    }

    @CtpUserComment(value="\u83b7\u53d6\u83b7\u53d6\u88ab spring \u7ba1\u7406\u7684\u6307\u5b9a\u7c7b\u522b\u7684 Bean \u5bf9\u8c61")
    public static <T> T getBean(Class<T> clazz) {
        return (T)Apps.getApplicationContext().getBean(clazz);
    }

    @CtpUserComment(value="\u83b7\u53d6\u6307\u5b9a\u540d\u79f0\u548c\u7c7b\u578b\u7684 Bean \u5bf9\u8c61\uff0c \u83b7\u53d6\u88ab spring \u7ba1\u7406\u7684 bean \u7684\u5bf9\u8c61")
    public static <T> T getBean(String beanName, Class<T> requiredType) {
        return (T)Apps.getApplicationContext().getBean(beanName, requiredType);
    }

    @CtpUserComment(value="\u8c03\u7528\u6307\u5b9a Bean \u7684\u6307\u5b9a\u65b9\u6cd5\u5e76\u8fd4\u56de\u7ed3\u679c\uff0c beanName \u662f\u4e3b\u670d\u52a1\u4e2d\u7684 bean\uff0cjar \u5305\u4e2d\u60f3\u7528\u65f6\u53ef\u4ee5\u901a\u8fc7\u6b64\u65b9\u6cd5\u8c03\u7528")
    public static <T> T invokeBean(String beanName, String methodName, Object ... params) {
        Object bean = Apps.getApplicationContext().getBean(beanName);
        StringBuilder logBuilder = new StringBuilder();
        try {
            logBuilder.append("\u8c03\u7528\u6307\u5b9aBean\u7684\u6307\u5b9a\u65b9\u6cd5,beanName:[" + beanName + "],methodName:[" + methodName + "], params:[" + JsonUtils.toJson((Object)params) + "]");
            Method method = ReflectUtil.getMethodByName(bean.getClass(), (String)methodName);
            Object invokeResult = ReflectUtil.invoke((Object)bean, (Method)method, (Object[])params);
            logBuilder.append("result:[" + JsonUtils.toJson((Object)invokeResult) + "]").append("result type:[" + (null == invokeResult ? "null" : invokeResult.getClass().getName()) + "]");
            log.info(logBuilder.toString());
            return (T)invokeResult;
        }
        catch (Exception e) {
            logBuilder.append("error:[" + e.getMessage() + "]");
            log.error(logBuilder.toString(), (Throwable)e);
            return null;
        }
    }

    @CtpUserComment(value="\u901a\u8fc7 key \u83b7\u53d6\u5c5e\u6027\u914d\u7f6e\u503c\uff0c \u5c5e\u6027\u914d\u7f6e\u53ef\u4ee5\u662f yaml \u6587\u4ef6\u4e5f\u53ef\u4ee5\u662f nacos \u914d\u7f6e")
    public static String getPropertyByName(String key) {
        return Apps.getApplicationContext().getEnvironment().getProperty(key);
    }

    @CtpUserComment(value="\u83b7\u53d6 request \u5bf9\u8c61")
    public static HttpServletRequest getRequest() {
        RequestAttributes requestAttributes = RequestContextHolder.getRequestAttributes();
        if (requestAttributes instanceof ServletRequestAttributes) {
            HttpServletRequest request = ((ServletRequestAttributes)requestAttributes).getRequest();
            log.info("get request: {}", (Object)request);
            return request;
        }
        log.info("get request: null (no ServletRequestAttributes found)");
        return null;
    }
}

