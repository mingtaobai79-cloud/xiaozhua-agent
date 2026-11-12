/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.boot.transport.Sort
 *  com.seeyon.udc.common.dto.EntityDto
 */
package com.seeyon.udc.api;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.boot.transport.Sort;
import com.seeyon.udc.common.dto.EntityDto;
import java.util.List;
import java.util.Map;

public interface EntityAppService {
    public SingleResponse<Long> create(SingleRequest<EntityDto> var1);

    public SingleResponse<Integer> update(SingleRequest<EntityDto> var1);

    public SingleResponse<Integer> deleteById(SingleRequest<Long> var1);

    public SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>> var1);

    public SingleResponse<EntityDto> selectById(SingleRequest<Long> var1);

    public ListResponse<EntityDto> selectByIds(SingleRequest<List<Long>> var1);

    public SingleResponse<EntityDto> selectByName(SingleRequest<Long> var1, SingleRequest<String> var2);

    public PageResponse<EntityDto> selectPageByCondition(PageRequest var1);

    public ListResponse<EntityDto> selectListByConditions(SingleRequest<Map<String, Object>> var1, Sort var2);

    public ListResponse<EntityDto> selectListByTerm(SingleRequest<Long> var1, SingleRequest<String> var2, Sort var3);

    public SingleResponse<EntityDto> selectParentById(SingleRequest<Long> var1);

    public ListResponse<EntityDto> selectEntitiesByAppId4Tree(SingleRequest<Long> var1);

    public ListResponse<EntityDto> selectAggregationEntitiesByAppId4Tree(SingleRequest<Long> var1);

    public PageResponse<EntityDto> selectChildrenByCondition(PageRequest var1);

    public ListResponse<EntityDto> selectPrimaryEntityByAppId(SingleRequest<Long> var1);

    public SingleResponse<EntityDto> selectByPrimaryEntityId(SingleRequest<Long> var1);

    public SingleResponse<Long> selectRootId(SingleRequest<Long> var1);

    public ListResponse<EntityDto> selectEntityByIdsLoadAttribute(SingleRequest<List<Long>> var1);
}
