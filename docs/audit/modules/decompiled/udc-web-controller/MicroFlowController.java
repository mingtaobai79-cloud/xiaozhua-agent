/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.HasRole
 *  com.seeyon.boot.annotation.MultiRequestBody
 *  com.seeyon.boot.annotation.ParameterInfo
 *  com.seeyon.boot.annotation.RestApi
 *  com.seeyon.boot.annotation.RestApiOperation
 *  com.seeyon.boot.starter.extmetadata.dto.UdcApplicationMetaDataDto
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.PageRequest
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.udc.api.MicroFlowInfoAppService
 *  com.seeyon.udc.appservice.MicroFlowAppService
 *  com.seeyon.udc.common.dto.EventQueryResultDto
 *  com.seeyon.udc.microflow.dto.CopyInfoBySourceIdDto
 *  com.seeyon.udc.microflow.dto.CopyInfoBySourceIdRespDto
 *  com.seeyon.udc.microflow.dto.CopyInfoDto
 *  com.seeyon.udc.microflow.dto.ListOperationTypeDto
 *  com.seeyon.udc.microflow.dto.MetaDataQueryDto
 *  com.seeyon.udc.microflow.dto.MicroFlowEventQueryDto
 *  com.seeyon.udc.microflow.dto.MicroFlowMsgDto
 *  com.seeyon.udc.microflow.dto.MicroFlowQueryDto
 *  com.seeyon.udc.microflow.dto.NodeQueryDto
 *  com.seeyon.udc.microflow.dto.NodeSchemaQueryDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowAppServiceMetaDataDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowCallInfoDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowDefinitionDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowItemDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowNodeDefinitionDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowOrderDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowServiceInfoDto
 *  com.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto
 *  com.seeyon.udc.microflow.dto.metadata.MfAggDtoMetadataDto
 *  com.seeyon.udc.microflow.dto.metadata.MfAggEntityItemDto
 *  com.seeyon.udc.microflow.dto.metadata.MfAppServiceMetadataDto
 *  com.seeyon.udc.microflow.dto.metadata.MfAppServiceMethodDto
 *  com.seeyon.udc.microflow.dto.metadata.MfDtoMetadataDto
 *  com.seeyon.udc.microflow.dto.metadata.MfDtoMetadataItemDto
 *  com.seeyon.udc.microflow.dto.metadata.MfFullAggDtoMetadataDto
 *  com.seeyon.udc.microflow.dto.metadata.MfJavaEnumDto
 *  com.seeyon.udc.microflow.dto.metadata.MfMqDto
 *  com.seeyon.udc.microflow.dto.metadata.MfRestDto
 *  com.seeyon.udc.microflow.dto.resp.CheckSchemaDto
 *  io.swagger.annotations.ApiParam
 *  javax.validation.constraints.NotNull
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.web.bind.annotation.GetMapping
 *  org.springframework.web.bind.annotation.PathVariable
 *  org.springframework.web.bind.annotation.PostMapping
 *  org.springframework.web.bind.annotation.RequestBody
 *  org.springframework.web.bind.annotation.RequestMapping
 *  org.springframework.web.bind.annotation.RestController
 */
package com.seeyon.udc.controller;

import com.seeyon.boot.annotation.HasRole;
import com.seeyon.boot.annotation.MultiRequestBody;
import com.seeyon.boot.annotation.ParameterInfo;
import com.seeyon.boot.annotation.RestApi;
import com.seeyon.boot.annotation.RestApiOperation;
import com.seeyon.boot.starter.extmetadata.dto.UdcApplicationMetaDataDto;
import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.PageRequest;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.udc.api.MicroFlowInfoAppService;
import com.seeyon.udc.appservice.MicroFlowAppService;
import com.seeyon.udc.common.dto.EventQueryResultDto;
import com.seeyon.udc.microflow.dto.CopyInfoBySourceIdDto;
import com.seeyon.udc.microflow.dto.CopyInfoBySourceIdRespDto;
import com.seeyon.udc.microflow.dto.CopyInfoDto;
import com.seeyon.udc.microflow.dto.ListOperationTypeDto;
import com.seeyon.udc.microflow.dto.MetaDataQueryDto;
import com.seeyon.udc.microflow.dto.MicroFlowEventQueryDto;
import com.seeyon.udc.microflow.dto.MicroFlowMsgDto;
import com.seeyon.udc.microflow.dto.MicroFlowQueryDto;
import com.seeyon.udc.microflow.dto.NodeQueryDto;
import com.seeyon.udc.microflow.dto.NodeSchemaQueryDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowAppServiceMetaDataDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowCallInfoDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowDefinitionDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowItemDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowNodeDefinitionDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowOrderDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowServiceInfoDto;
import com.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto;
import com.seeyon.udc.microflow.dto.metadata.MfAggDtoMetadataDto;
import com.seeyon.udc.microflow.dto.metadata.MfAggEntityItemDto;
import com.seeyon.udc.microflow.dto.metadata.MfAppServiceMetadataDto;
import com.seeyon.udc.microflow.dto.metadata.MfAppServiceMethodDto;
import com.seeyon.udc.microflow.dto.metadata.MfDtoMetadataDto;
import com.seeyon.udc.microflow.dto.metadata.MfDtoMetadataItemDto;
import com.seeyon.udc.microflow.dto.metadata.MfFullAggDtoMetadataDto;
import com.seeyon.udc.microflow.dto.metadata.MfJavaEnumDto;
import com.seeyon.udc.microflow.dto.metadata.MfMqDto;
import com.seeyon.udc.microflow.dto.metadata.MfRestDto;
import com.seeyon.udc.microflow.dto.resp.CheckSchemaDto;
import io.swagger.annotations.ApiParam;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(value={"udc/microflow"})
@RestApi(value="微流程管理接口", group="微流程")
@HasRole(value={"udcAppDesigner", "udcSystemAdmin"})
public class MicroFlowController {
    @Autowired
    private MicroFlowAppService microFlowAppService;
    @Autowired
    private MicroFlowInfoAppService microFlowInfoAppService;

    @RestApiOperation(value="1.1根据微流程ID获取微流程")
    @GetMapping(value={"findById/{id}"})
    public SingleResponse<MicroFlowDefinitionDto> getMicroFlowDefinition(@PathVariable(value="id") Long id) {
        return this.microFlowAppService.getMicroFlowDefinition(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="1.2根据条件获取分页微流程列表")
    @PostMapping(value={"search"})
    public PageResponse<MicroFlowItemDto> selectPageByCondition(@RequestBody PageRequest request) {
        return this.microFlowAppService.selectListByCondition(request);
    }

    @RestApiOperation(value="1.3根据条件获取微流程列表")
    @PostMapping(value={"search-no-page"})
    public ListResponse<MicroFlowItemDto> selectPageByCondition(@RequestBody MicroFlowQueryDto queryDto) {
        return this.microFlowAppService.selectListByQuery(SingleRequest.from((Object)queryDto));
    }

    @RestApiOperation(value="1.4校验微流程Schema")
    @PostMapping(value={"checkSchema"})
    public SingleResponse<CheckSchemaDto> checkSchema(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.checkSchema(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="1.5校验并更新微流程")
    @PostMapping(value={"checkSchema/update"})
    public SingleResponse<CheckSchemaDto> checkSchemaAndUpdate(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.checkSchemaAndUpdate(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="1.6新建微流程（强制草稿态）")
    @PostMapping(value={"create"})
    public SingleResponse<Long> create(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.create(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="1.7更新微流程（强制草稿态）")
    @PostMapping(value={"update"})
    public SingleResponse<Integer> update(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.update(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="1.8更新微流程排序号和分组")
    @PostMapping(value={"update/order-no-and-group"})
    public SingleResponse<Integer> updateOrderNoAndGroup(@RequestBody MicroFlowOrderDto request) {
        return this.microFlowAppService.updateOrderNoAndGroup(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="1.9批量移动微流程")
    @PostMapping(value={"batch-move"})
    public SingleResponse<Integer> batchMove(@RequestBody List<MicroFlowOrderDto> request) {
        return this.microFlowAppService.batchMove(SingleRequest.from(request));
    }

    @RestApiOperation(value="1.10根据微流程标题查询")
    @PostMapping(value={"search/term"})
    public PageResponse<MicroFlowItemDto> searchListByCaption(@RequestBody PageRequest request) {
        return this.microFlowAppService.searchListByCaption(request);
    }

    @RestApiOperation(value="1.11获取某一sourceId下所有微流程的详细信息")
    @GetMapping(value={"select-details/{sourceId}"})
    public ListResponse<MicroFlowDefinitionDto> selectDetailsBySourceId(@PathVariable(value="sourceId") String sourceId) {
        return this.microFlowAppService.selectDetailsBySourceId(SingleRequest.from((Object)sourceId));
    }

    @RestApiOperation(value="1.12停用上一版本元数据")
    @PostMapping(value={"disable-last-version-metadata"})
    public SingleResponse<Integer> disableLastVersionMetadata(@ApiParam(value="微流程id") @MultiRequestBody @NotNull Long id) {
        return this.microFlowAppService.disableLastVersionMetadata(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="2.0根据实体id查询实体业务规则")
    @PostMapping(value={"search/entityRule"})
    public PageResponse<MicroFlowItemDto> selectEntityRulePageByEntityId(@RequestBody PageRequest request) {
        return this.microFlowAppService.selectEntityRulePageByEntityId(request);
    }

    @RestApiOperation(value="2.1根据sourceId删除微流程")
    @PostMapping(value={"delete-by-source-id"})
    public SingleResponse<Boolean> deleteBySourceId(@ApiParam(value="sourceId") @MultiRequestBody @NotNull String sourceId) {
        return this.microFlowAppService.deleteBySourceId(SingleRequest.from((Object)sourceId));
    }

    @RestApiOperation(value="2.2根据id删除微流程")
    @PostMapping(value={"delete"})
    public SingleResponse<Boolean> deleteById(@ApiParam(value="微流程id") @MultiRequestBody @NotNull Long id) {
        return this.microFlowAppService.deleteById(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="2.21根据ids删除微流程")
    @PostMapping(value={"delete-by-ids"})
    public SingleResponse<Integer> deleteByIds(@ApiParam(value="微流程ids") @MultiRequestBody @NotNull List<Long> ids) {
        return this.microFlowAppService.deleteByIds(SingleRequest.from(ids));
    }

    @RestApiOperation(value="2.4获取列表操作分组下拉数据")
    @GetMapping(value={"listOperationType"})
    public ListResponse<ListOperationTypeDto> getListOperationType() {
        return this.microFlowAppService.getListOperationTypes();
    }

    @RestApiOperation(value="2.5分页获取后台已发布服务定义微流程")
    @PostMapping(value={"service/list"})
    public PageResponse<MicroFlowSubMfDto> selectServiceMicroFlowPageByAppId(@RequestBody PageRequest request) {
        return this.microFlowAppService.selectServiceMicroFlowPageByAppId(request);
    }

    @RestApiOperation(value="2.5.1分页获取后台已发布服务定义微流程(后端子微流程)")
    @PostMapping(value={"service/list/sub-mf"})
    public PageResponse<MicroFlowSubMfDto> selectSubMfPageByAppId(@RequestBody PageRequest request) {
        return this.microFlowAppService.selectSubMfPageByAppId(request);
    }

    @RestApiOperation(value="2.6获取服务定义微流程详情")
    @GetMapping(value={"service/details/{id}"})
    public SingleResponse<MicroFlowServiceInfoDto> getServiceById(@PathVariable(value="id") Long id) {
        return this.microFlowAppService.getServiceInfoById(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="2.6.1获取服务定义微流程详情(个性化应用)")
    @PostMapping(value={"service/details/dynamic"})
    public SingleResponse<MicroFlowServiceInfoDto> getServiceByIdAndHostAppName(@RequestBody MetaDataQueryDto params) {
        return this.microFlowAppService.getServiceInfoByParams(SingleRequest.from((Object)params));
    }

    @RestApiOperation(value="2.7检查微流程显示名称是否已存在")
    @PostMapping(value={"check/micro-flow/caption"})
    public SingleResponse<Boolean> checkMicroFlowCaptionIsExists(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.checkMicroFlowCaptionIsExists(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="2.8检查微流程名称是否已存在")
    @PostMapping(value={"check/micro-flow/name"})
    public SingleResponse<Boolean> checkMicroFlowNameIsExists(@RequestBody MicroFlowDefinitionDto request) {
        return this.microFlowAppService.checkMicroFlowNameIsExists(SingleRequest.from((Object)request));
    }

    @RestApiOperation(value="2.9获取元数据格式的微流程AppService")
    @GetMapping(value={"/app-service/{id}"})
    public SingleResponse<MicroFlowAppServiceMetaDataDto> getMicroFlowAppServiceMetaDataBoById(@PathVariable(value="id") Long microFlowId) {
        return this.microFlowAppService.getMicroFlowAppServiceMetaDataBoById(SingleRequest.from((Object)microFlowId));
    }

    @RestApiOperation(value="3.01复制微流程")
    @PostMapping(value={"/copy"})
    public SingleResponse<Long> copy(@RequestBody CopyInfoDto copyInfoDto) {
        return this.microFlowAppService.copy(SingleRequest.from((Object)copyInfoDto));
    }

    @RestApiOperation(value="3.02根据sourceId复制微流程")
    @PostMapping(value={"/copyBySourceId"})
    public ListResponse<CopyInfoBySourceIdRespDto> copyBySourceId(@RequestBody CopyInfoBySourceIdDto dto) {
        return this.microFlowAppService.copyBySourceId(SingleRequest.from((Object)dto));
    }

    @RestApiOperation(value="3.03复制控件绑定的页面规则")
    @PostMapping(value={"copy/page-rule-bound-control"})
    public ListResponse<CopyInfoBySourceIdRespDto> copyPageRuleBoundControl(@MultiRequestBody @ApiParam(value="原始页面规则ID集合") List<Long> originPageRuleIdList, @MultiRequestBody @ApiParam(value="新页面ID") String newSourceId) {
        return this.microFlowAppService.copyPageRuleBoundControl(originPageRuleIdList, newSourceId);
    }

    @RestApiOperation(value="3.04根据应用appName查询自定义DTO列表")
    @PostMapping(value={"/search/nonEntityDto"})
    public ListResponse<MfDtoMetadataItemDto> searchNonEntityDtoByAppName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectNonEntityTreeExcludeBoot(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.05根据元数据DtoFullName查询封装DTO元数据")
    @PostMapping(value={"/find/customDto"})
    public SingleResponse<MfDtoMetadataDto> findCustomDto(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.findCustomDto(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.06根据应用appName查询实体DTO树")
    @PostMapping(value={"/search/treeEntity"})
    public ListResponse<MfAggEntityItemDto> searchTreeEntity(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchEntityTree(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.07根据DtoFullname和应用name查询appService")
    @PostMapping(value={"/search/appService"})
    public SingleResponse<MfAppServiceMetadataDto> searchAppService(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchAppService(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.08根据appName查找下面的AppService列表")
    @PostMapping(value={"/search/appService-by-appName"})
    public ListResponse<MfAppServiceMetadataDto> searchAppServiceByAppName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchAppServiceByAppName(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.09根据serviceName查询AppService信息")
    @PostMapping(value={"/search/appService-by-name"})
    public SingleResponse<MfAppServiceMetadataDto> searchAppServiceByName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchAppServiceByName(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.10根据methodName查询method详情")
    @PostMapping(value={"/search/method-by-name"})
    public SingleResponse<MfAppServiceMethodDto> searchMethodByName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchMethodByName(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.11根据实体fullName对应的dto")
    @PostMapping(value={"/find/dto-by-entity"})
    public SingleResponse<MfDtoMetadataDto> findDtoByEntity(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.findDtoByEntity(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="3.12根据聚合DTO的fullName批量查询聚合DTO信息")
    @PostMapping(value={"/batch-find/agg-dto"})
    public ListResponse<MfAggDtoMetadataDto> selectMfAggDtoByAggDtoFullNameList(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectMfAggDtoByAggDtoFullNameList(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.0查询指定服务Rest信息(排除组件)")
    @PostMapping(value={"/search/rest-exclude-boot"})
    public ListResponse<MfRestDto> searchRestExcludeBoot(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchRestWithOutBoot(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.1过滤实体事件消息")
    @PostMapping(value={"/filter/event"})
    public ListResponse<EventQueryResultDto> filterEvent(@RequestBody MicroFlowEventQueryDto paramDto) {
        return this.microFlowAppService.filterEvent(SingleRequest.from((Object)paramDto));
    }

    @RestApiOperation(value="4.2过滤系统MQ信息")
    @PostMapping(value={"/filter/mq"})
    public ListResponse<MfMqDto> filterSystemMqInfo(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.filterSystemMqInfo(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.3根据appName查询枚举")
    @PostMapping(value={"/search/enum-by-appName"})
    public ListResponse<MfJavaEnumDto> searchEnumByAppName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchEnumByAppName(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.4根据enumName查询枚举详情")
    @PostMapping(value={"/find/enum-by-name"})
    public SingleResponse<MfJavaEnumDto> findEnumByName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.findEnumByName(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.5应用列表查询(包含扩展)")
    @PostMapping(value={"/search/apps"})
    public ListResponse<UdcApplicationMetaDataDto> searchApps(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchApps(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.6不可用节点")
    @PostMapping(value={"/disable-node"})
    public ListResponse<MicroFlowNodeDefinitionDto> getDisableNodes(@RequestBody NodeQueryDto query) {
        return this.microFlowAppService.getDisableNodes(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.7查询当前应用的实体DTO树")
    @PostMapping(value={"/tree-entity-dto"})
    public ListResponse<MfAggEntityItemDto> searchTreeEntityDto(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchEntityDtoTree(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.8可消息投递的mq列表")
    @PostMapping(value={"/search/send-mq-list"})
    public ListResponse<MfMqDto> sendMqList(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchMqList(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.9获取微流程事件列表")
    @PostMapping(value={"/search/event-list"})
    public ListResponse<MfDtoMetadataItemDto> searchMicroFlowEventList(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.searchMicroFlowEventList(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="4.10创建消息对象")
    @PostMapping(value={"create-message"})
    public SingleResponse<Long> createMessage(@RequestBody MicroFlowMsgDto dto) {
        return this.microFlowAppService.createMessage(SingleRequest.from((Object)dto));
    }

    @RestApiOperation(value="5.0修改消息对象")
    @PostMapping(value={"update-message"})
    public SingleResponse<Integer> updateMessage(@RequestBody MicroFlowMsgDto dto) {
        return this.microFlowAppService.updateMessage(SingleRequest.from((Object)dto));
    }

    @RestApiOperation(value="5.1查询某一应用下的微流程消息对象")
    @GetMapping(value={"search-micro-flow-message/{appId}"})
    public ListResponse<MicroFlowMsgDto> selectMicroFlowMessageByAppId(@PathVariable(value="appId") @ApiParam(value="应用 ID") Long appId) {
        return this.microFlowAppService.searchMsgByAppId(SingleRequest.from((Object)appId));
    }

    @RestApiOperation(value="5.2查询某一应用下的微流程事件对象")
    @GetMapping(value={"search-micro-flow-event/{appId}"})
    public ListResponse<MicroFlowMsgDto> selectMicroFlowEventByAppId(@PathVariable(value="appId") @ApiParam(value="应用 ID") Long appId) {
        return this.microFlowAppService.searchEventByAppId(SingleRequest.from((Object)appId));
    }

    @RestApiOperation(value="5.3根据id删除消息对象")
    @PostMapping(value={"message-dto/delete"})
    public SingleResponse<Integer> deleteMessageById(@ParameterInfo(value="事件id") @MultiRequestBody @NotNull Long id) {
        return this.microFlowAppService.deleteMessageById(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="5.4根据应用appName查询消息对象列表")
    @PostMapping(value={"/search/message-dto"})
    public ListResponse<MfDtoMetadataItemDto> searchMessageDtoByAppName(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectMessageExcludeBoot(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="5.5获取消息对象详情及其属性信息")
    @GetMapping(value={"select-message/{id}"})
    public SingleResponse<MicroFlowMsgDto> selectMessageDtoWithAttrsById(@PathVariable(value="id") Long id) {
        return this.microFlowAppService.getMessageById(SingleRequest.from((Object)id));
    }

    @RestApiOperation(value="5.6检查对象元数据是否存在")
    @PostMapping(value={"check/dto-metadata/exist"})
    public SingleResponse<Boolean> checkDtoMetadataExist(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.checkDtoMetaDataExist(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="5.6获取前端页面规则子流程下拉列表")
    @PostMapping(value={"service/frontend/list"})
    public PageResponse<MicroFlowSubMfDto> selectServiceFrontendPageBySourceId(@RequestBody PageRequest request) {
        return this.microFlowAppService.selectFrontendServiceMicroFlowPageBySourceId(request);
    }

    @RestApiOperation(value="5.7根据聚合DTO的fullName批量查询Java枚举信息")
    @PostMapping(value={"/batch-find/java-enum"})
    public ListResponse<MfJavaEnumDto> selectMfJavaEnumByAggDtoFullNameList(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectMfJavaEnumByAggDtoFullNameList(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="5.8根据DTO的fullName查询全量聚合DTO信息")
    @PostMapping(value={"/find/full-agg-dto"})
    public SingleResponse<MfFullAggDtoMetadataDto> selectMfFullAggDto(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectMfFullAggDto(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="5.9获取某个DTO对象的数据体系")
    @PostMapping(value={"/find/data-system"})
    public ListResponse<Set<String>> selectDataSystemInfo(@RequestBody MetaDataQueryDto query) {
        return this.microFlowAppService.selectDataSystemInfo(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="5.10过滤非虚拟DTO")
    @PostMapping(value={"/filter/not-virtual"})
    public ListResponse<String> filterNotVirtualDto(@RequestBody List<String> javaTypeList) {
        return this.microFlowAppService.filterNotVirtualDto(SingleRequest.from(javaTypeList));
    }

    @RestApiOperation(value="6.1获取某一微流程的上游调用信息")
    @PostMapping(value={"find/call-info/upstream"})
    public ListResponse<MicroFlowCallInfoDto> findUpstreamCallInfo(@MultiRequestBody @ApiParam(value="当前应用ID") Long appId, @MultiRequestBody @ApiParam(value="选定微流程的ID") Long mfId) {
        return this.microFlowAppService.findUpstreamCallInfo(appId, mfId);
    }

    @RestApiOperation(value="6.2获取某一微流程的下游调用信息")
    @PostMapping(value={"find/call-info/downstream"})
    public ListResponse<MicroFlowCallInfoDto> findDownstreamCallInfo(@MultiRequestBody @ApiParam(value="当前应用ID") Long appId, @MultiRequestBody @ApiParam(value="选定微流程的ID") Long mfId) {
        return this.microFlowAppService.findDownstreamCallInfo(appId, mfId);
    }

    @RestApiOperation(value="6.3根据条件获取节点 Schema 信息")
    @PostMapping(value={"find/node-schema"})
    public ListResponse<String> findNodeSchemaByCondition(@RequestBody NodeSchemaQueryDto query) {
        return this.microFlowAppService.findNodeSchemaByCondition(SingleRequest.from((Object)query));
    }

    @RestApiOperation(value="6.4根据条件查询微流程全量（仅前端生成代码使用,大字段只查询dataSchema）")
    @PostMapping(value={"select-by-condition-for-deploy"})
    public ListResponse<MicroFlowDefinitionDto> selectListByCondition4Deploy(@RequestBody MicroFlowQueryDto queryDto) {
        return ListResponse.from((List)this.microFlowAppService.selectListByCondition4Deploy(SingleRequest.from((Object)queryDto)));
    }

    @RestApiOperation(value="6.5获取调用拓展代码的自定义服务节点信息")
    @GetMapping(value={"select-call-extend-app-service/{appId}"})
    public SingleResponse<Map<String, List<String>>> findCallExtendAppServiceNode(@PathVariable(value="appId") Long appId) {
        return this.microFlowAppService.findCallExtendAppServiceNode(SingleRequest.from((Object)appId));
    }

    @RestApiOperation(value="6.6获取微流程中使用的所有连接器信息")
    @GetMapping(value={"select-call-connector-app-service/{appId}"})
    public SingleResponse<Map<String, List<String>>> findCallConnectorAppService(@PathVariable(value="appId") Long appId) {
        return this.microFlowInfoAppService.findCallConnectorAppService(SingleRequest.from((Object)appId));
    }

    @RestApiOperation(value="还原微流程", description="还原微流程")
    @PostMapping(value={"/recover"})
    public SingleResponse<MicroFlowItemDto> recover(@MultiRequestBody @ApiParam(value="变更记录id") Long id, @MultiRequestBody @ApiParam(value="变更记录id") Long domainId) {
        return this.microFlowAppService.recover(id, domainId);
    }

    @RestApiOperation(value="测试引用了实体的", description="测试引用了实体的")
    @GetMapping(value={"/test/entityRef/{appId}"})
    public SingleResponse<Map<Long, List<Map<String, Object>>>> entityRef(@PathVariable Long appId) {
        return SingleResponse.from((Object)this.microFlowAppService.getUsedEntityActionByAppId(SingleRequest.from((Object)appId)));
    }
}
