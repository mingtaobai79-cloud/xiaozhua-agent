/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.context.Apps
 *  com.seeyon.boot.domain.dao.support.DatabaseType
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.appservice.ex.parser.DBExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.DMExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.KingBaseExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.MysqlExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.OracleExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.PGExceptionParser
 *  com.seeyon.boot.starter.appservice.ex.parser.impl.SqlServerExceptionParser
 *  com.seeyon.boot.starter.eventbus.exception.EventBusException
 *  org.mybatis.spring.MyBatisSystemException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.dao.DataIntegrityViolationException
 *  org.springframework.dao.DuplicateKeyException
 *  org.springframework.jdbc.BadSqlGrammarException
 */
package com.seeyon.boot.starter.appservice.ex;

import com.seeyon.boot.context.Apps;
import com.seeyon.boot.domain.dao.support.DatabaseType;
import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.appservice.ex.parser.DBExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.DMExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.KingBaseExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.MysqlExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.OracleExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.PGExceptionParser;
import com.seeyon.boot.starter.appservice.ex.parser.impl.SqlServerExceptionParser;
import com.seeyon.boot.starter.eventbus.exception.EventBusException;
import org.mybatis.spring.MyBatisSystemException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.BadSqlGrammarException;

public class ExceptionTransfer {
    private static final Logger log = LoggerFactory.getLogger(ExceptionTransfer.class);
    private static DBExceptionParser parser;

    public static Throwable transferExceptionIfNecessary(Throwable throwable) {
        if (throwable.getCause() instanceof DuplicateKeyException) {
            throwable = throwable.getCause();
        }
        if (throwable.getCause() != null && throwable.getCause().getCause() instanceof DuplicateKeyException) {
            throwable = throwable.getCause().getCause();
        }
        if (throwable.getCause() instanceof DataIntegrityViolationException) {
            throwable = throwable.getCause();
        }
        if (throwable.getCause() != null && throwable.getCause().getCause() instanceof DataIntegrityViolationException) {
            throwable = throwable.getCause().getCause();
        }
        if (throwable instanceof EventBusException) {
            throwable = throwable.getCause();
        }
        BusinessException businessException = null;
        if (throwable instanceof DuplicateKeyException || throwable instanceof DataIntegrityViolationException || throwable instanceof BadSqlGrammarException) {
            log.error("数据库异常", throwable);
            businessException = ExceptionTransfer.getDBExceptionParser().parser(throwable.getMessage());
            if (businessException == null) {
                businessException = new BusinessException("BOOT_4009");
            }
            return businessException;
        }
        if (throwable instanceof MyBatisSystemException) {
            log.error("数据库异常", throwable);
            BusinessException exception = new BusinessException("BOOT_4000", throwable);
            return exception;
        }
        return throwable;
    }

    private static DBExceptionParser getDBExceptionParser() {
        if (parser == null) {
            parser = Apps.getDatabaseType() == DatabaseType.postgresql ? new PGExceptionParser() : (Apps.getDatabaseType() == DatabaseType.oracle ? new OracleExceptionParser() : (Apps.getDatabaseType() == DatabaseType.sqlserver ? new SqlServerExceptionParser() : (Apps.getDatabaseType() == DatabaseType.dm7 || Apps.getDatabaseType() == DatabaseType.dm8 ? new DMExceptionParser() : (Apps.getDatabaseType() == DatabaseType.kingbasev8 ? new KingBaseExceptionParser() : new MysqlExceptionParser()))));
        }
        return parser;
    }
}
