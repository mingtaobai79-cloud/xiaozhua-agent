/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.appservice.ex.parser.DBExceptionParser
 *  com.seeyon.boot.util.StringUtils
 */
package com.seeyon.boot.starter.appservice.ex.parser.impl;

import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.appservice.ex.parser.DBExceptionParser;
import com.seeyon.boot.util.StringUtils;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class DMExceptionParser
implements DBExceptionParser {
    private static Pattern KEY_PATTERN = Pattern.compile("唯一性约束条件\\[(.+?)\\]");
    private static Pattern DM_UK_PATTERN_EN = Pattern.compile("Violate unique constraint on \\[(.*?)\\]\\[(.*?)\\]");
    private static Pattern RANG_PATTERN = Pattern.compile("ParameterMapping\\{property='(.+?)'");
    private static Pattern TOO_LONG_PATTERN = Pattern.compile("列\\[(.+?)\\]长度超出定义");
    private static Pattern UNKNOWN_COLUMN_PATTERN = Pattern.compile("无效的列名\\[(.+?)\\]");
    private static Pattern UNKNOWN_TABLE_PATTERN = Pattern.compile("无效的表或视图名\\[(.+?)\\]");
    private static Pattern NOT_NULL_PATTERN = Pattern.compile("违反列\\[(.+?)\\]非空约束");

    public BusinessException parser(String message) {
        if (message.contains("数字溢出")) {
            String column = this.exPattern(message, RANG_PATTERN);
            return new BusinessException("BOOT_4100", new String[]{column});
        }
        if (message.contains("长度超出定义") || message.contains("Record length exceed maximum size")) {
            String column = this.exPattern(message, TOO_LONG_PATTERN);
            return new BusinessException("BOOT_4100", new String[]{column});
        }
        if (message.contains("无效的列名")) {
            String column = this.exPattern(message, UNKNOWN_COLUMN_PATTERN);
            return new BusinessException("BOOT_4201", new String[]{column});
        }
        if (message.contains("无效的表或视图名")) {
            String column = this.exPattern(message, UNKNOWN_TABLE_PATTERN);
            return new BusinessException("BOOT_4200", new String[]{column});
        }
        if (message.contains("非空约束")) {
            String column = this.exPattern(message, NOT_NULL_PATTERN);
            return new BusinessException("BOOT_4101", new String[]{column});
        }
        if (message.contains("唯一性约束条件") || message.contains("Violate unique constraint on ")) {
            String ukName = this.exPattern(message, KEY_PATTERN);
            if (StringUtils.isNotBlank((CharSequence)ukName)) {
                if (!ukName.toUpperCase().startsWith("UK_")) {
                    ukName = "PRIMARY";
                }
            } else {
                ukName = this.exPattern(message, DM_UK_PATTERN_EN, 2);
                if (StringUtils.isNotBlank((CharSequence)ukName) && !ukName.toUpperCase().startsWith("UK_")) {
                    ukName = "PRIMARY";
                }
            }
            if (StringUtils.isNotBlank((CharSequence)ukName)) {
                return new BusinessException("BOOT_4004").addError(ukName);
            }
        }
        return null;
    }

    private String exPattern(String message, Pattern pattern) {
        return this.exPattern(message, pattern, 1);
    }

    private String exPattern(String message, Pattern pattern, int index) {
        String str = "";
        Matcher ukMatcher = pattern.matcher(message);
        while (ukMatcher.find()) {
            str = ukMatcher.group(index);
        }
        if (str.indexOf(".") > -1) {
            str = str.split("\\.")[1];
        }
        return str;
    }
}
