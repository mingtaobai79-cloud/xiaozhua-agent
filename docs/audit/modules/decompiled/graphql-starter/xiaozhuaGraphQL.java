/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.conifg.SystemProperties
 *  com.seeyon.boot.starter.graphql.GraphQLProperties
 *  com.seeyon.boot.starter.graphql.GraphQLProvider
 *  com.seeyon.boot.starter.graphql.SeeyonGraphQL$1
 *  com.seeyon.boot.starter.graphql.parse.SeeyonParser
 *  com.seeyon.boot.starter.graphql.util.SeeyonThreadPool
 *  graphql.ExecutionInput
 *  graphql.ExecutionResult
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.stereotype.Component
 */
package com.seeyon.boot.starter.graphql;

import com.seeyon.boot.conifg.SystemProperties;
import com.seeyon.boot.starter.graphql.GraphQLProperties;
import com.seeyon.boot.starter.graphql.GraphQLProvider;
import com.seeyon.boot.starter.graphql.SeeyonGraphQL;
import com.seeyon.boot.starter.graphql.parse.SeeyonParser;
import com.seeyon.boot.starter.graphql.util.SeeyonThreadPool;
import graphql.ExecutionInput;
import graphql.ExecutionResult;
import java.util.concurrent.CompletableFuture;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class SeeyonGraphQL {
    private static final Logger log = LoggerFactory.getLogger(SeeyonGraphQL.class);
    @Autowired
    private GraphQLProvider graphQLProvider;
    @Autowired
    private SeeyonParser parser;
    @Autowired
    private SeeyonThreadPool pool;
    @Autowired
    private GraphQLProperties graphQLProperties;
    @Autowired
    private SystemProperties systemProperties;

    public ExecutionResult execute(ExecutionInput executionInput, String appName) {
        ExecutionResult validateResult;
        CompletableFuture<ExecutionResult> validateFuture = this.validate(executionInput, appName);
        ExecutionResult fetcherResult = this.fetcher(executionInput, appName);
        if (null != validateFuture && (validateResult = validateFuture.join()).getErrors() != null) {
            return validateResult;
        }
        return fetcherResult;
    }

    private CompletableFuture<ExecutionResult> validate(ExecutionInput executionInput, String appName) {
        if (this.systemProperties.getPerformance().booleanValue()) {
            return null;
        }
        return CompletableFuture.supplyAsync(() -> this.graphQLProvider.graphQL(appName).seeyonValidate(executionInput));
    }

    private ExecutionResult fetcher(ExecutionInput executionInput, String appName) {
        try {
            return this.parser.parseAndExe(executionInput, appName);
        }
        catch (Exception e) {
            if (null == e.getMessage()) {
                log.error("GraphQL数据获取空指针异常:", (Throwable)e);
            }
            1 result = new /* Unavailable Anonymous Inner Class!! */;
            return result;
        }
    }
}
