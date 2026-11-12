/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.commons.text.CaseUtils
 */
package com.seeyon.boot.starter.graphql.util;

import org.apache.commons.text.CaseUtils;

public class GraphQLTypeNameUtil {
    public static String touchName(String dtoFullName, String appName, boolean isInput) {
        String s = GraphQLTypeNameUtil.appNameToCamel(appName) + GraphQLTypeNameUtil.getSimpleNameFromFullName(dtoFullName);
        if (isInput) {
            s = s + "InputBody";
        }
        return s.replaceAll("[^A-Za-z0-9]", "");
    }

    private static String appNameToCamel(String appName) {
        return CaseUtils.toCamelCase((String)appName, (boolean)true, (char[])new char[]{'-'});
    }

    private static String getSimpleNameFromFullName(String fullName) {
        return fullName;
    }
}
