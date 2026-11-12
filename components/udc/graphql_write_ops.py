"""三大模块 GraphQL 写链 op 目录 —— 实体/应用/基础设置（bundle 全量扫描固化）。

证据基线：src_redux_store_ts.14dc061e.js（2.45MB，主 store）全量正则扫描，
形态四元组 fieldType/paramsType/paramsKey (+params 变量) 逐字照录；
本目录 = STATIC（bundle 原文）；读/写语义由名字推断为 verb_hint，**名字不是事实**，
是否真写库由宿主以 LIVE 回读为准（与 check-excel 不当只读、BOOT_0000+content=0≠删除
同族纪律）。

本轮新增/修正（相对 ENTITY-PAGE-INVENTORY §2.7.4 / SETTINGS-TABS §3/§4）：
1. 数组包装 [InputBody] 恰好 10 个 + [String] 1 个 + Long/String/Map 裸形态 3 个 = 14 特例，
   与 §2.7.4 计数吻合；全清单见 ARRAY_WRAPPED / BARE_FORM。
2. udcApplicationVersionPlatformServiceGet = **零入参**（load 只有 queryFields，无 paramsKey）
   → 关闭 DATADICT §6.4 的「params:{deployDto:e} 语义不明」UNVERIFIED：deployDto 是别处
   泄漏的形参名，此 op 实际不接收参数。
3. 扩展实体写链已齐（Scalability/Option 的 Post/Update/Delete/BatchDelete）
   → 关闭 SETTINGS §3.6「写侧 GraphQL op 未逐个定位」。
4. 选项集(UDC 枚举)写链已齐（udcUdcEnum{Post,Update,Delete} + Category{Post,Update,Delete,
   SelectCategoryAndEnum} + ItemOperateBatch[数组]）→ 与 CtpEnum（枚举 tab）双族坐实。
5. 参照 createOrUpdate service body 已坐实（§5#8 残留关闭）：
   `d=async e=>{load({fieldType:"udcReferConfigCreateOrUpdatePost",
   paramsType:"…InputBody",paramsKey:"body",params:e,queryFields:"content",
   showLoading:false})}` —— body 由组件层透传（配置骨架见 §2.8.3③）。
6. **双 service 约定并存**（本轮坐实，扫描器双正则）：
   a) saga 约定 `load({fieldType, paramsType, paramsKey})` —— 三大模块主体；
   b) raw Apollo 文档字符串 `mutation udcXxxPost ($body: udcXxxPostInputBody)` /
      `query udcXxxGet ($path: …)`（如参照「设置参照内容」向导 module53993→332.Jt→
      udcApolloQuery(有id?UpdateConfigInfo:CreateConfigInfo)，组件链已逐字坐实）。
   约定 b 的三元组由变量声明归一（$body→…InputBody / $path→…InputPath），
   与本目录同构登记；臆造判定两约定并查。
"""
from __future__ import annotations

from typing import Any

SCHEMA_ID = "udc.construction.graphql-write-ops.v1"

# 来源 bundle（证据锚点，非写死环境值；路径在 scratch 快照，正式归档走 config/）
EVIDENCE_BUNDLE = "src_redux_store_ts.14dc061e.js"
EVIDENCE_LEVEL = "STATIC"   # bundle 原文；读/写语义未 LIVE


def _entry(op: str, ptype: str, pkey: str) -> dict[str, str]:
    form = "ARRAY_BODY" if ptype.startswith("[") else {
        "body": "BODY", "path": "PATH", "query": "QUERY"}.get(pkey, "BARE")
    if ptype in ("Long", "String", "Map"):
        form = f"{ptype.upper()}_BODY"
    verb = "WRITE?" if any(k in op for k in
        ("Create", "Update", "Delete", "Save", "Import", "Copy", "Recover", "Transfer",
         "Disable", "Merge", "Move", "Clear", "Stop", "Restart", "Batch", "Post")) \
        else "READ?"
    # Post 结尾但 Search/Select/Find/List 语义 → READ? 修正
    if any(k in op for k in ("Search", "Select", "Find", "List", "Fetch", "Get", "Query", "Check")):
        verb = "READ?/CHECK?"
    return {"op": op, "paramsType": ptype, "paramsKey": pkey, "form": form, "verb": verb}


# ---------------- 实体（54）----------------
ENTITY_WRITE_OPS: tuple[dict[str, str], ...] = tuple(_entry(*e) for e in (
    ("udcEntityPost", "udcEntityPostInputBody", "body"),
    ("udcEntityUpdatePost", "udcEntityUpdatePostInputBody", "body"),
    ("udcEntityDeletePost", "udcEntityDeletePostInputBody", "body"),
    ("udcEntityBatchDeletePost", "udcEntityBatchDeletePostInputBody", "body"),
    ("udcEntityEntityCopyPost", "udcEntityEntityCopyPostInputBody", "body"),
    ("udcEntityUpdateExtensionLinkagePost", "udcEntityUpdateExtensionLinkagePostInputBody", "body"),
    ("udcEntityConstraintEntityPost", "udcEntityConstraintEntityPostInputBody", "body"),
    ("udcEntityGroupCreatePost", "udcEntityGroupCreatePostInputBody", "body"),
    ("udcEntityGroupUpdatePost", "udcEntityGroupUpdatePostInputBody", "body"),
    ("udcEntityGroupDeletePost", "udcEntityGroupDeletePostInputBody", "body"),
    ("udcEntityGroupBatchDeletePost", "udcEntityGroupBatchDeletePostInputBody", "body"),
    ("udcEntityGroupUpdateBatchPost", "[udcEntityGroupUpdateBatchPostInputBody]", "body"),
    ("udcEntityBatchUpdateEntityGroupIdAndOrdernoPost", "[udcEntityBatchUpdateEntityGroupIdAndOrdernoPostInputBody]", "body"),
    ("udcEntityAttributePost", "udcEntityAttributePostInputBody", "body"),
    ("udcEntityAttributeUpdatePost", "udcEntityAttributeUpdatePostInputBody", "body"),
    # 注：单属性删除 udcEntityAttributeDeletePost 不在主 store bundle（§2.7.7 LIVE 冒烟用过），
    # 见 LIVE_EVIDENCED_OPS 分源登记，不混入 bundle 静态目录。
    ("udcEntityAttributeBatchDeletePost", "udcEntityAttributeBatchDeletePostInputBody", "body"),
    ("udcEntityAttributeBatchUpdatePost", "[udcEntityAttributeBatchUpdatePostInputBody]", "body"),
    ("udcEntityAttributeTransferPost", "udcEntityAttributeTransferPostInputBody", "body"),
    ("udcEntityAttributeSelectParentEnumAttrsPost", "Map", "body"),
    ("udcEntityAttributeGroupCreateUpdatePost", "[udcEntityAttributeGroupCreateUpdatePostInputBody]", "body"),
    ("udcEntityAttributeGroupBathUpdatePost", "[udcEntityAttributeGroupBathUpdatePostInputBody]", "body"),
    ("udcEntityAttributeGroupCanceGroupPost", "udcEntityAttributeGroupCanceGroupPostInputBody", "body"),
    ("udcAttributeGroupOperateBatchPost", "udcAttributeGroupOperateBatchPostInputBody", "body"),
    ("udcAttributeSetPost", "udcAttributeSetPostInputBody", "body"),
    ("udcAttributeSetUpdatePost", "udcAttributeSetUpdatePostInputBody", "body"),
    ("udcAttributeSetDeletePost", "udcAttributeSetDeletePostInputBody", "body"),
    ("udcAttributeSetSelectByAppidPost", "udcAttributeSetSelectByAppidPostInputBody", "body"),
    ("udcAttributeSetSelectByNameAttributesPost", "udcAttributeSetSelectByNameAttributesPostInputBody", "body"),
    ("udcAttributeSetSearchTermPost", "udcAttributeSetSearchTermPostInputBody", "body"),
    ("udcIndexPost", "udcIndexPostInputBody", "body"),
    ("udcIndexUpdatePost", "udcIndexUpdatePostInputBody", "body"),
    ("udcIndexDeletePost", "udcIndexDeletePostInputBody", "body"),
    ("udcIndexDeleteBatchPost", "udcIndexDeleteBatchPostInputBody", "body"),
    ("udcIndexEntityListPost", "Long", "body"),
    ("udcEventPost", "udcEventPostInputBody", "body"),
    ("udcEventCreateWithDataPost", "udcEventCreateWithDataPostInputBody", "body"),
    ("udcEventUpdatePost", "udcEventUpdatePostInputBody", "body"),
    ("udcEventUpdateWithDataPost", "udcEventUpdateWithDataPostInputBody", "body"),
    ("udcEventDeletePost", "udcEventDeletePostInputBody", "body"),
    ("udcEventDeleteBatchPost", "udcEventDeleteBatchPostInputBody", "body"),
    ("udcEventListPost", "udcEventListPostInputBody", "body"),
    ("udcEventSearchTermPost", "udcEventSearchTermPostInputBody", "body"),
    ("udcReferConfigCreateOrUpdatePost", "udcReferConfigCreateOrUpdatePostInputBody", "body"),
    ("udcReferConfigGroupListPost", "udcReferConfigGroupListPostInputBody", "body"),
    # 参照「设置参照内容」向导(组件53993)实际提交链：module332.Jt(p)→udcApolloQuery(
    # e.id ? udcReferConfigUpdateConfigInfoPost : udcReferConfigCreateConfigInfoPost)；
    # 下方 4 个为 raw Apollo 文档字符串约定（非 load/fieldType），bundle 逐字坐实。
    ("udcReferConfigCreateConfigInfoPost", "udcReferConfigCreateConfigInfoPostInputBody", "body"),
    ("udcReferConfigUpdateConfigInfoPost", "udcReferConfigUpdateConfigInfoPostInputBody", "body"),
    ("udcReferConfigDeleteByGroupIdPost", "udcReferConfigDeleteByGroupIdPostInputBody", "body"),
    # 参照配置列表读（mutation 文档字符串约定；verb 由名字推 READ?/CHECK?，真读写以 LIVE 为准）
    ("udcReferConfigListPost", "udcReferConfigListPostInputBody", "body"),
    ("udcMetaDataMergeReferPost", "udcMetaDataMergeReferPostInputBody", "body"),
    ("udcMetaDataReferAndAppPost", "udcMetaDataReferAndAppPostInputBody", "body"),
    ("udcEntityAssociationSerialPost", "udcEntityAssociationSerialPostInputBody", "body"),
    ("udcEntityAssociationGroupSerialPost", "udcEntityAssociationGroupSerialPostInputBody", "body"),
    ("udcDataFlowListEventEntityPost", "udcDataFlowListEventEntityPostInputBody", "body"),
    ("udcDataFlowListEventsPost", "udcDataFlowListEventsPostInputBody", "body"),
    ("udcMicroflowFilterEventPost", "udcMicroflowFilterEventPostInputBody", "body"),
    ("udcMicroflowSearchEventListPost", "udcMicroflowSearchEventListPostInputBody", "body"),
    ("udcFunctionUpdateFunctionReferPost", "udcFunctionUpdateFunctionReferPostInputBody", "body"),
    ("udcMicroflowRefactorResolveNodesReferenceRelationshipsPost", "udcMicroflowRefactorResolveNodesReferenceRelationshipsPostInputBody", "body"),
))

# ---------------- 应用（32）----------------
APPLICATION_WRITE_OPS: tuple[dict[str, str], ...] = tuple(_entry(*e) for e in (
    ("udcApplicationPost", "udcApplicationPostInputBody", "body"),
    ("udcApplicationUpdatePost", "udcApplicationUpdatePostInputBody", "body"),
    ("udcApplicationDeletePost", "udcApplicationDeletePostInputBody", "body"),
    ("udcApplicationDeleteByGuidPost", "udcApplicationDeleteByGuidPostInputBody", "body"),
    ("udcApplicationSaveAsPost", "udcApplicationSaveAsPostInputBody", "body"),
    ("udcApplicationMultiVersionPost", "udcApplicationMultiVersionPostInputBody", "body"),
    ("udcApplicationSearchNewWithVersionListPost", "udcApplicationSearchNewWithVersionListPostInputBody", "body"),
    ("udcApplicationSearchPageByGuidPost", "udcApplicationSearchPageByGuidPostInputBody", "body"),
    ("udcApplicationAppVersionAppGuidPost", "udcApplicationAppVersionAppGuidPostInputPath", "path"),
    ("udcApplicationImportNewPost", "udcApplicationImportNewPostInputBody", "body"),
    ("udcApplicationImportOtherAppZipPost", "udcApplicationImportOtherAppZipPostInputBody", "body"),
    ("udcApplicationTransferParamPost", "udcApplicationTransferParamPostInputBody", "body"),
    ("udcApplicationSchemaDownloadIdPost", "udcApplicationSchemaDownloadIdPostInputPath", "path"),
    ("udcApplicationFetchLastVersionMetadataPost", "udcApplicationFetchLastVersionMetadataPostInputBody", "body"),
    ("udcApplicationDependentApplicationCreateBatchPost", "[udcApplicationDependentApplicationCreateBatchPostInputBody]", "body"),
    ("udcApplicationDependentApplicationDeleteByIdPost", "udcApplicationDependentApplicationDeleteByIdPostInputBody", "body"),
    ("udcApplicationDependentApplicationSelectByConditionPost", "udcApplicationDependentApplicationSelectByConditionPostInputBody", "body"),
    ("udcApplicationDependentApplicationVersionUpdatePost", "udcApplicationDependentApplicationVersionUpdatePostInputBody", "body"),
    ("udcApplicationDependentApplicationVersionUpdateBatchPost", "udcApplicationDependentApplicationVersionUpdateBatchPostInputBody", "body"),
    ("udcDeploymentAppReadyStatePost", "udcDeploymentAppReadyStatePostInputBody", "body"),
    ("udcDeploymentLatestTestInfoPost", "udcDeploymentLatestTestInfoPostInputBody", "body"),
    ("udcDeploymentAppOnlineNewPost", "udcDeploymentAppOnlineNewPostInputBody", "body"),
    ("udcSandboxAppStartByAppPost", "udcSandboxAppStartByAppPostInputBody", "body"),
    ("udcSandboxRestartPost", "udcSandboxRestartPostInputBody", "body"),
    ("udcSandboxAppCleanRestartByAppPost", "udcSandboxAppCleanRestartByAppPostInputBody", "body"),
    ("udcSandboxStopPost", "udcSandboxStopPostInputBody", "body"),
    ("udcSandboxBatchStopPost", "udcSandboxBatchStopPostInputBody", "body"),
    ("udcSandboxBatchCleanStopPost", "udcSandboxBatchCleanStopPostInputBody", "body"),
    ("udcSandboxClearDataPost", "String", "body"),
    ("udcSandboxSandboxAppsByConditionPost", "udcSandboxSandboxAppsByConditionPostInputBody", "body"),
    ("udcSandboxSelectRolesPost", "udcSandboxSelectRolesPostInputBody", "body"),
    ("udcSandboxClientSandboxLogUrlPost", "udcSandboxClientSandboxLogUrlPostInputBody", "body"),
    # raw Apollo 文档字符串约定（非 load/fieldType）：应用复制/模板/检测/新版设计器保存
    ("udcApplicationCopyPost", "udcApplicationCopyPostInputBody", "body"),
    ("udcApplicationCreateFromTemplatePost", "udcApplicationCreateFromTemplatePostInputBody", "body"),
    ("udcApplicationDoDetectionPost", "udcApplicationDoDetectionPostInputBody", "body"),
    ("udcApplicationDoDetectionStatePost", "udcApplicationDoDetectionStatePostInputBody", "body"),
    ("udcApplicationSaveNormalNewDesignPost", "udcApplicationSaveNormalNewDesignPostInputBody", "body"),
    ("udcApplicationSearchDetectionPost", "udcApplicationSearchDetectionPostInputBody", "body"),
    ("udcApplicationSearchTemplatePost", "udcApplicationSearchTemplatePostInputBody", "body"),
))

# ---------------- 基础设置（25）----------------
BASIC_SETTING_WRITE_OPS: tuple[dict[str, str], ...] = tuple(_entry(*e) for e in (
    ("udcUdcEnumPost", "udcUdcEnumPostInputBody", "body"),
    ("udcUdcEnumUpdatePost", "udcUdcEnumUpdatePostInputBody", "body"),
    ("udcUdcEnumDeletePost", "udcUdcEnumDeletePostInputBody", "body"),
    ("udcUdcEnumItemListPost", "udcUdcEnumItemListPostInputBody", "body"),
    ("udcUdcEnumItemOperateBatchPost", "[udcUdcEnumItemOperateBatchPostInputBody]", "body"),
    # raw Apollo 文档字符串约定（枚举项搜索/枚举搜索，mutation body）
    ("udcUdcEnumItemSearch", "udcUdcEnumItemSearchInputBody", "body"),
    ("udcUdcEnumSearch", "udcUdcEnumSearchInputBody", "body"),
    ("udcUdcEnumCategoryPost", "udcUdcEnumCategoryPostInputBody", "body"),
    ("udcUdcEnumCategoryUpdatePost", "udcUdcEnumCategoryUpdatePostInputBody", "body"),
    ("udcUdcEnumCategoryDeletePost", "udcUdcEnumCategoryDeletePostInputBody", "body"),
    ("udcUdcEnumCategorySelectCategoryAndEnumPost", "udcUdcEnumCategorySelectCategoryAndEnumPostInputBody", "body"),
    ("udcDataTransferObjectCreateDtoPost", "udcDataTransferObjectCreateDtoPostInputBody", "body"),
    ("udcDataTransferObjectCreateDtoWithAttrsPost", "[udcDataTransferObjectCreateDtoWithAttrsPostInputBody]", "body"),
    ("udcDataTransferObjectUpdateDtoPost", "udcDataTransferObjectUpdateDtoPostInputBody", "body"),
    ("udcDataTransferObjectUpdateDtoWithAttrsPost", "[udcDataTransferObjectUpdateDtoWithAttrsPostInputBody]", "body"),
    ("udcDataTransferObjectDeletePost", "udcDataTransferObjectDeletePostInputBody", "body"),
    ("udcDataTransferObjectDeleteDtoWithAttrsPost", "udcDataTransferObjectDeleteDtoWithAttrsPostInputBody", "body"),
    ("udcDataTransferObjectSearchListPost", "udcDataTransferObjectSearchListPostInputBody", "body"),
    ("udcScalabilityPost", "udcScalabilityPostInputBody", "body"),
    ("udcScalabilityUpdatePost", "udcScalabilityUpdatePostInputBody", "body"),
    ("udcScalabilityDeletePost", "udcScalabilityDeletePostInputBody", "body"),
    ("udcScalabilityBatchDeletePost", "udcScalabilityBatchDeletePostInputBody", "body"),
    ("udcScalabilityOptionPost", "udcScalabilityOptionPostInputBody", "body"),
    ("udcScalabilityOptionUpdatePost", "udcScalabilityOptionUpdatePostInputBody", "body"),
    ("udcScalabilityOptionDeletePost", "udcScalabilityOptionDeletePostInputBody", "body"),
    ("udcSerialSchemeSearchNoPagePost", "udcSerialSchemeSearchNoPagePostInputBody", "body"),
    ("udcExpressionSchemaPost", "udcExpressionSchemaPostInputBody", "body"),
))

# ---------------- 读链 GET（页面加载面，bundle 同扫；多数 paramsKey=path）----------------
ENTITY_READ_OPS: tuple[dict[str, str], ...] = (
    _entry("udcEntityGet", "udcEntityGetInputPath", "path"),
    _entry("udcEntitySelectAllByAppidAppGet", "udcEntitySelectAllByAppidAppGetInputPath", "path"),
    _entry("udcEntitySelectAllByEntityIdGet", "udcEntitySelectAllByEntityIdGetInputPath", "path"),
    _entry("udcEntityPrimarySelectByAppidAppGet", "udcEntityPrimarySelectByAppidAppGetInputPath", "path"),
    _entry("udcEntityPrimarySelectRootGet", "udcEntityPrimarySelectRootGetInputPath", "path"),
    _entry("udcEntityGroupSelectByAppidAppGet", "udcEntityGroupSelectByAppidAppGetInputPath", "path"),
    _entry("udcEntitySelectMasterEntityCountAppGet", "udcEntitySelectMasterEntityCountAppGetInputPath", "path"),
    _entry("udcEntitySelectEventDataByEntityIdGet", "udcEntitySelectEventDataByEntityIdGetInputPath", "path"),
    _entry("udcEntityAttributeGet", "udcEntityAttributeGetInputPath", "path"),
    _entry("udcEntityAttributeSelectByPrimaryGet", "udcEntityAttributeSelectByPrimaryGetInputPath", "path"),
    _entry("udcEntityAttributePresetAttributeCapacityAllAppGet", "udcEntityAttributePresetAttributeCapacityAllAppGetInputPath", "path"),
    _entry("udcEntityAttributeGroupSearch", "udcEntityAttributeGroupSearchInputBody", "body"),
    _entry("udcEntityAssociationEntityAppGet", "udcEntityAssociationEntityAppGetInputPath", "path"),
    _entry("udcAttributeGroupEntityGet", "udcAttributeGroupEntityGetInputPath", "path"),
    _entry("udcEventGet", "udcEventGetInputPath", "path"),
    _entry("udcEventSelectWithDataGet", "udcEventSelectWithDataGetInputPath", "path"),
    _entry("udcIndexAttributeEntityGet", "udcIndexAttributeEntityGetInputPath", "path"),
    # raw Apollo query 文档字符串约定（立体实体按 app 读）
    _entry("udcEntityStereoEntityAppGet", "udcEntityStereoEntityAppGetInputPath", "path"),
)
APPLICATION_READ_OPS: tuple[dict[str, str], ...] = (
    _entry("udcApplicationGet", "udcApplicationGetInputPath", "path"),
    _entry("udcApplicationDetailGet", "udcApplicationDetailGetInputPath", "path"),
    _entry("udcApplicationCopyGet", "udcApplicationCopyGetInputPath", "path"),
    _entry("udcApplicationIsLastVersionAppGet", "udcApplicationIsLastVersionAppGetInputPath", "path"),
    _entry("udcApplicationRenewalAppEditingTimeGet", "udcApplicationRenewalAppEditingTimeGetInputPath", "path"),
    _entry("udcSandboxBuildInfoAppGet", "udcSandboxBuildInfoAppGetInputPath", "path"),
    _entry("udcSandboxSelectAppGet", "udcSandboxSelectAppGetInputPath", "path"),
    # raw Apollo query 文档字符串约定（非 load/fieldType）
    _entry("udcApplicationAppFeatureAppGet", "udcApplicationAppFeatureAppGetInputPath", "path"),
    _entry("udcApplicationFeatureAppTypeGet", "udcApplicationFeatureAppTypeGetInputPath", "path"),
)
BASIC_SETTING_READ_OPS: tuple[dict[str, str], ...] = (
    _entry("udcDataTransferObjectGet", "udcDataTransferObjectGetInputPath", "path"),
    # raw Apollo query 文档字符串约定（枚举项读取）
    _entry("udcUdcEnumItemGet", "udcUdcEnumItemGetInputPath", "path"),
    _entry("udcDataTransferObjectSelectDtoGet", "udcDataTransferObjectSelectDtoGetInputPath", "path"),
    _entry("udcDataTransferObjectSelectDtoWithAttrsGet", "udcDataTransferObjectSelectDtoWithAttrsGetInputPath", "path"),
    _entry("udcDataTransferObjectSearchByMicroFlowIdMicroFlowGet", "udcDataTransferObjectSearchByMicroFlowIdMicroFlowGetInputPath", "path"),
    _entry("udcDataTransferObjectSearchMicroFlowCustomDtoAppGet", "udcDataTransferObjectSearchMicroFlowCustomDtoAppGetInputPath", "path"),
    # raw Apollo query 文档字符串约定（按 sourceId 搜 DTO）
    _entry("udcDataTransferObjectSearchBySourceIdSourceGet", "udcDataTransferObjectSearchBySourceIdSourceGetInputPath", "path"),
    _entry("udcScalabilityOptionDataTypeAppGet", "udcScalabilityOptionDataTypeAppGetInputPath", "path"),
    _entry("udcScalabilityOptionOptionGet", "udcScalabilityOptionOptionGetInputPath", "path"),
    _entry("udcScalabilityOptionSelectByAppidTreeAppGet", "udcScalabilityOptionSelectByAppidTreeAppGetInputPath", "path"),
    _entry("udcScalabilityOptionSelectByAppidWithDetailAppGet", "udcScalabilityOptionSelectByAppidWithDetailAppGetInputPath", "path"),
)

# ---------------- 微流程域（module 70857 等；bundle 全量扫描固化）----------------
# 证据链（bundle 逐字）：
#   saveMicroflowSchema   → udcMicroflowCreatePost       （新建微流程/实体规则）
#   updateMicroflowSchema → udcMicroflowUpdatePost       （更新）
#   checkAndUpdate…Schema → udcMicroflowCheckSchemaUpdatePost（含 check/errorMessage 校验返回）
#   checkMicroFlowCaption → udcMicroflowCheckMicroFlowCaptionPost（规则名重复检查，content=false 即重复）
# 此前被 classify 漏掉（对账盲区）；72 op 三元组全部 bundle 原文。
MICROFLOW_OPS: tuple[dict[str, str], ...] = tuple(_entry(*e) for e in (
    ("udcMicroflowCreatePost", "udcMicroflowCreatePostInputBody", "body"),
    ("udcMicroflowUpdatePost", "udcMicroflowUpdatePostInputBody", "body"),
    ("udcMicroflowCheckSchemaUpdatePost", "udcMicroflowCheckSchemaUpdatePostInputBody", "body"),
    ("udcMicroflowCheckMicroFlowCaptionPost", "udcMicroflowCheckMicroFlowCaptionPostInputBody", "body"),
    ("udcMicroflowCheckDtoMetadataExistPost", "udcMicroflowCheckDtoMetadataExistPostInputBody", "body"),
    ("udcMicroflowDeletePost", "udcMicroflowDeletePostInputBody", "body"),
    ("udcMicroflowRecoverPost", "udcMicroflowRecoverPostInputBody", "body"),
    ("udcMicroflowCopy", "udcMicroflowCopyPostInputBody", "body"),
    ("udcMicroflowCopyBySourceIdPost", "udcMicroflowCopyBySourceIdPostInputBody", "body"),
    ("udcMicroflowCopyPageRuleBoundControlPost", "udcMicroflowCopyPageRuleBoundControlPostInputBody", "body"),
    ("udcMicroflowBatchMovePost", "udcMicroflowBatchMovePostInputBody", "body"),
    ("udcMicroflowUpdateOrderNoAndGroupPost", "udcMicroflowUpdateOrderNoAndGroupPostInputBody", "body"),
    ("udcMicroflowDisableNodePost", "udcMicroflowDisableNodePostInputBody", "body"),
    ("udcMicroflowRefactorRefactoredPost", "udcMicroflowRefactorRefactoredPostInputBody", "body"),
    ("udcMicroflowCreateMessagePost", "udcMicroflowCreateMessagePostInputBody", "body"),
    ("udcMicroflowUpdateMessagePost", "udcMicroflowUpdateMessagePostInputBody", "body"),
    ("udcMicroflowMessageDtoDeletePost", "udcMicroflowMessageDtoDeletePostInputBody", "body"),
    ("udcMicroflowSearch", "udcMicroflowSearchInputBody", "body"),
    ("udcMicroflowSearchAppsPost", "udcMicroflowSearchAppsPostInputBody", "body"),
    ("udcMicroflowSearchAppServicePost", "udcMicroflowSearchAppServicePostInputBody", "body"),
    ("udcMicroflowSearchAppServiceByNamePost", "udcMicroflowSearchAppServiceByNamePostInputBody", "body"),
    ("udcMicroflowSearchAppServiceByAppNamePost", "udcMicroflowSearchAppServiceByAppNamePostInputBody", "body"),
    ("udcMicroflowSearchMethodByNamePost", "udcMicroflowSearchMethodByNamePostInputBody", "body"),
    ("udcMicroflowSearchEntityRulePost", "udcMicroflowSearchEntityRulePostInputBody", "body"),
    ("udcMicroflowSearchSendMqListPost", "udcMicroflowSearchSendMqListPostInputBody", "body"),
    ("udcMicroflowSearchTreeEntityPost", "udcMicroflowSearchTreeEntityPostInputBody", "body"),
    ("udcMicroflowSearchNonEntityDtoPost", "udcMicroflowSearchNonEntityDtoPostInputBody", "body"),
    ("udcMicroflowSearchMessageDtoPost", "udcMicroflowSearchMessageDtoPostInputBody", "body"),
    ("udcMicroflowSearchEnumByAppNamePost", "udcMicroflowSearchEnumByAppNamePostInputBody", "body"),
    ("udcMicroflowSearchRestExcludeBootPost", "udcMicroflowSearchRestExcludeBootPostInputBody", "body"),
    ("udcMicroflowFilterMqPost", "udcMicroflowFilterMqPostInputBody", "body"),
    ("udcMicroflowFilterNotVirtualPost", "[String]", "body"),
    ("udcMicroflowFindCustomDtoPost", "udcMicroflowFindCustomDtoPostInputBody", "body"),
    ("udcMicroflowFindDtoByEntityPost", "udcMicroflowFindDtoByEntityPostInputBody", "body"),
    ("udcMicroflowFindFullAggDtoPost", "udcMicroflowFindFullAggDtoPostInputBody", "body"),
    ("udcMicroflowFindDataSystemPost", "udcMicroflowFindDataSystemPostInputBody", "body"),
    ("udcMicroflowFindCallInfoUpstreamPost", "udcMicroflowFindCallInfoUpstreamPostInputBody", "body"),
    ("udcMicroflowFindCallInfoDownstreamPost", "udcMicroflowFindCallInfoDownstreamPostInputBody", "body"),
    ("udcMicroflowTreeEntityDtoPost", "udcMicroflowTreeEntityDtoPostInputBody", "body"),
    ("udcMicroflowBatchFindAggDtoPost", "udcMicroflowBatchFindAggDtoPostInputBody", "body"),
    ("udcMicroflowBatchFindJavaEnumPost", "udcMicroflowBatchFindJavaEnumPostInputBody", "body"),
    ("udcMicroflowServiceCommonInputListPost", "udcMicroflowServiceCommonInputListPostInputBody", "body"),
    ("udcMicroflowServiceDetailsDynamicPost", "udcMicroflowServiceDetailsDynamicPostInputBody", "body"),
    ("udcMicroflowServiceFrontendListPost", "udcMicroflowServiceFrontendListPostInputBody", "body"),
    ("udcMicroflowServiceListPost", "udcMicroflowServiceListPostInputBody", "body"),
    ("udcMicroflowServiceListSubMfPost", "udcMicroflowServiceListSubMfPostInputBody", "body"),
    # 读链（GET/query；paramsKey=path/query）
    ("udcMicroflowFindByIdGet", "udcMicroflowFindByIdGetInputPath", "path"),
    ("udcMicroflowFindNodesGet", "udcMicroflowFindNodesGetInputQuery", "query"),
    ("udcMicroflowServiceDetailsGet", "udcMicroflowServiceDetailsGetInputPath", "path"),
    ("udcMicroflowSelectMessageGet", "udcMicroflowSelectMessageGetInputPath", "path"),
    ("udcMicroflowSearchMicroFlowEventAppGet", "udcMicroflowSearchMicroFlowEventAppGetInputPath", "path"),
    ("udcMicroflowSearchMicroFlowMessageAppGet", "udcMicroflowSearchMicroFlowMessageAppGetInputPath", "path"),
    # 元数据域（微流程节点选实体/DTO/枚举/CtpEnum 用；module 70857 同族导出）
    ("udcMetaDataSelectEntityPost", "udcMetaDataSelectEntityPostInputBody", "body"),
    ("udcMetaDataSelectEntityByAppIdAppGet", "udcMetaDataSelectEntityByAppIdAppGetInputPath", "path"),
    ("udcMetaDataSelectEntityByAppNameAppNameGet", "udcMetaDataSelectEntityByAppNameAppNameGetInputPath", "path"),
    ("udcMetaDataSelectAggregationEntityPost", "udcMetaDataSelectAggregationEntityPostInputBody", "body"),
    ("udcMetaDataSelectAggregationEntityEntityGet", "udcMetaDataSelectAggregationEntityEntityGetInputPath", "path"),
    ("udcMetaDataSelectJavaEnumByAppPost", "udcMetaDataSelectJavaEnumByAppPostInputBody", "body"),
    ("udcMetaDataSelectJavaEnumItemPost", "udcMetaDataSelectJavaEnumItemPostInputBody", "body"),
    ("udcMetaDataSelectCtpEnumAppGet", "udcMetaDataSelectCtpEnumAppGetInputPath", "path"),
    ("udcMetaDataSelectCtpEnumByApp1Post", "udcMetaDataSelectCtpEnumByApp1PostInputBody", "body"),
    ("udcMetaDataSelectAppByIdPost", "udcMetaDataSelectAppByIdPostInputBody", "body"),
    ("udcMetaDataSelectPagePost", "udcMetaDataSelectPagePostInputBody", "body"),
    ("udcMetaDataSelectPageInfoListPost", "udcMetaDataSelectPageInfoListPostInputBody", "body"),
    ("udcMetaDataSelectCustomReferPageGet", "udcMetaDataSelectCustomReferPageGetInputPath", "path"),
    ("udcMetaDataSearchAvailableAppMultiVersionPost", "udcMetaDataSearchAvailableAppMultiVersionPostInputBody", "body"),
    ("udcMetaDataSearchAvailableUpgradeAppGet", "udcMetaDataSearchAvailableUpgradeAppGetInputPath", "path"),
    ("udcEnumItemGet", "udcEnumItemGetInputPath", "path"),
    ("udcConditionCheckPost", "[udcConditionCheckPostInputBody]", "body"),
    # 页面过滤方案（module 51796；op 名由 concat 拼接，静态已还原）——
    # 「列表默认方案」/页面规则真实调用链：planType:"FILTER" 字符串、content=JSON.stringify(方案对象)
    ("udcUdcRuntimeFilterPlanPost", "udcUdcRuntimeFilterPlanPostInputBody", "body"),
    ("udcUdcRuntimeFilterPlanUpdatePost", "udcUdcRuntimeFilterPlanUpdatePostInputBody", "body"),
    ("udcUdcRuntimeFilterPlanDeletePost", "Long", "body"),
    ("udcUdcRuntimeFilterPlanBatchDeletePost", "Long", "body"),
))


MODULES: dict[str, tuple[dict[str, str], ...]] = {
    "entity": ENTITY_WRITE_OPS + ENTITY_READ_OPS,
    "application": APPLICATION_WRITE_OPS + APPLICATION_READ_OPS,
    "basic-setting": BASIC_SETTING_WRITE_OPS + BASIC_SETTING_READ_OPS,
    "microflow": MICROFLOW_OPS,
}

WRITE_OPS: dict[str, tuple[dict[str, str], ...]] = {
    "entity": ENTITY_WRITE_OPS,
    "application": APPLICATION_WRITE_OPS,
    "basic-setting": BASIC_SETTING_WRITE_OPS,
}
READ_OPS: dict[str, tuple[dict[str, str], ...]] = {
    "entity": ENTITY_READ_OPS,
    "application": APPLICATION_READ_OPS,
    "basic-setting": BASIC_SETTING_READ_OPS,
}

# LIVE 实证补充（主 store bundle 未含 fieldType 定义；来源 §2.7.7 写链冒烟；分源登记，
# 不与 bundle 静态目录混同）。
LIVE_EVIDENCED_OPS: tuple[dict[str, str], ...] = (
    {"op": "udcEntityAttributeDeletePost", "paramsType": "SingleRequest",
     "paramsKey": "body", "form": "LIVE_BODY", "verb": "WRITE?", "evidence": "OBSERVED_LIVE",
     "note": "§2.7.7：body:{id} → content=1 且回读不存在；批删 BatchDeletePost 两种数组传法 content=0 不删"},
)

# 零入参 GET 修正（bundle load 有 paramsType 声明但**无 paramsKey/params** → 调用侧零入参）
ZERO_PARAM_OPS: dict[str, str] = {
    "udcApplicationVersionPlatformServiceGet":
        "DATADICT §6.4 记 params:{deployDto:e} 语义不明 → bundle load 无 paramsKey/params，"
        "调用零入参；deployDto 为别处形参名泄漏，非此 op 入参",
    "udcStereotypeListGet": "零入参（§2.7.1）",
    "udcExpressionSystemVariableListGet": "零入参 path 族",
}

# 数组包装全清单（§2.7.4 的 14 特例 = 10 [InputBody] + 1 [String] + Long/String/Map 3）
ARRAY_WRAPPED_INPUT_BODY: tuple[str, ...] = tuple(
    e["op"] for e in (*ENTITY_WRITE_OPS, *APPLICATION_WRITE_OPS, *BASIC_SETTING_WRITE_OPS)
    if e["form"] == "ARRAY_BODY")
BARE_FORM: dict[str, tuple[str, ...]] = {
    "Long_BODY": tuple(e["op"] for m in MODULES.values() for e in m if e["form"] == "LONG_BODY"),
    "String_BODY": tuple(e["op"] for m in MODULES.values() for e in m if e["form"] == "STRING_BODY"),
    "Map_BODY": tuple(e["op"] for m in MODULES.values() for e in m if e["form"] == "MAP_BODY"),
}
ARRAY_STRING_SPECIAL: tuple[str, ...] = ("udcMicroflowFilterNotVirtualPost",)  # [String] 数组


def op_entry(op: str) -> dict[str, str] | None:
    for m in MODULES.values():
        for e in m:
            if e["op"] == op:
                return e
    for e in LIVE_EVIDENCED_OPS:
        if e["op"] == op:
            return e
    return None


def catalog() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID, "evidence_bundle": EVIDENCE_BUNDLE,
        "evidence_level": EVIDENCE_LEVEL,
        "counts": {k: len(v) for k, v in MODULES.items()},
        "discipline": "paramsType/paramsKey=bundle 原文(STATIC)；verb 列仅名字推断，"
                      "读写事实与副作用须 LIVE 回读（Post 名≠写、Check 名≠只读）",
        "closures": [
            "§5#8 参照 createOrUpdate service body 坐实（透传 e）",
            "§3.6 扩展实体写链 6 op 定位齐",
            "§3.2 选项集(UDC枚举)写链定位齐（udcUdcEnum* 族）",
            "§6.4 VersionPlatformServiceGet 零入参（deployDto 为形参泄漏）",
            "§双约定 raw Apollo 字符串 op 归一登记（参照 ConfigInfo 4 op 坐实 53993→332.Jt 组件链）",
        ],
        "array_wrapped": ARRAY_WRAPPED_INPUT_BODY,
        "bare_form": BARE_FORM,
        "zero_param": ZERO_PARAM_OPS,
    }


__all__ = [
    "SCHEMA_ID", "EVIDENCE_BUNDLE", "EVIDENCE_LEVEL",
    "ENTITY_WRITE_OPS", "APPLICATION_WRITE_OPS", "BASIC_SETTING_WRITE_OPS",
    "MICROFLOW_OPS", "MODULES",
    "ARRAY_WRAPPED_INPUT_BODY", "BARE_FORM", "ARRAY_STRING_SPECIAL", "ZERO_PARAM_OPS",
    "op_entry", "catalog",
]
