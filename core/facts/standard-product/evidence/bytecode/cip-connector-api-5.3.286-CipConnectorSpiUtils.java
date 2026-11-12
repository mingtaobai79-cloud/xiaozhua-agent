/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  cn.hutool.core.util.ReflectUtil
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.util.JsonUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.seeyon.cip.connector.common;

import cn.hutool.core.util.ReflectUtil;
import com.seeyon.boot.context.Apps;
import com.seeyon.boot.util.JsonUtils;
import java.lang.reflect.Method;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CipConnectorSpiUtils {
    private static final Logger log = LoggerFactory.getLogger(CipConnectorSpiUtils.class);
    private static final Map<String, Object> instances = new ConcurrentHashMap<String, Object>();

    private void CipConnectorSpiUtils() {
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
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

    public static <T> T getBean(Class<T> clazz) {
        return (T)Apps.getApplicationContext().getBean(clazz);
    }

    public static <T> T getBean(String beanName, Class<T> requiredType) {
        return (T)Apps.getApplicationContext().getBean(beanName, requiredType);
    }

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

    public static String getPropertyByName(String key) {
        return Apps.getApplicationContext().getEnvironment().getProperty(key);
    }
}

