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

public class MysqlExceptionParser
implements DBExceptionParser {
    private static Pattern KEY_PATTERN = Pattern.compile("for key '(.+?)'");
    private static Pattern RANG_PATTERN = Pattern.compile("Out of range value for column '(.+?)' at row");
    private static Pattern TOO_LONG_PATTERN = Pattern.compile("Data too long for column '(.+?)' at row");
    private static Pattern UNKNOWN_COLUMN_PATTERN = Pattern.compile("Unknown column '(.+?)' in");
    private static Pattern UNKNOWN_TABLE_PATTERN = Pattern.compile("Table '(.+?)' doesn't exist");
    private static Pattern NOT_NULL_PATTERN = Pattern.compile("Column '(.+?)' cannot be null");

    public BusinessException parser(String message) {
        String ukName;
        if (message.contains("Out of range value for column")) {
            String column = this.exPattern(message, RANG_PATTERN);
            return new BusinessException("BOOT_4100", new String[]{column});
        }
        if (message.contains("Data too long for column")) {
            String column = this.exPattern(message, TOO_LONG_PATTERN);
            return new BusinessException("BOOT_4100", new String[]{column});
        }
        if (message.contains("Unknown column ")) {
            String column = this.exPattern(message, UNKNOWN_COLUMN_PATTERN);
            return new BusinessException("BOOT_4201", new String[]{column});
        }
        if (message.contains(" doesn't exist")) {
            String column = this.exPattern(message, UNKNOWN_TABLE_PATTERN);
            return new BusinessException("BOOT_4200", new String[]{column});
        }
        if (message.contains(" cannot be null")) {
            String column = this.exPattern(message, NOT_NULL_PATTERN);
            return new BusinessException("BOOT_4101", new String[]{column});
        }
        if (message.contains(" for key ") && StringUtils.isNotBlank((CharSequence)(ukName = this.exPattern(message, KEY_PATTERN)))) {
            return new BusinessException("BOOT_4004").addError(ukName);
        }
        return null;
    }

    private String exPattern(String message, Pattern pattern) {
        String str = "";
        Matcher ukMatcher = pattern.matcher(message);
        while (ukMatcher.find()) {
            str = ukMatcher.group(1);
        }
        if (str.indexOf(".") > -1) {
            str = str.split("\\.")[1];
        }
        return str;
    }
}
