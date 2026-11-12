/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.starter.graphql.execution.SeeyonSchema
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.stereotype.Component
 */
package com.seeyon.boot.starter.graphql.execution;

import com.seeyon.boot.starter.graphql.execution.SeeyonSchema;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class SeeyonSchemaService {
    private static final Logger log = LoggerFactory.getLogger(SeeyonSchemaService.class);
    static Map<String, SeeyonSchema> schemaCache = new HashMap<String, SeeyonSchema>();

    public void add(String appName, SeeyonSchema schema) {
        schemaCache.put(appName, schema);
    }

    public SeeyonSchema get(String appName) {
        return schemaCache.get(appName);
    }
}
