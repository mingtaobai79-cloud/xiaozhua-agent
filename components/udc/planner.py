from dataclasses import dataclass, field
@dataclass
class UdcPlan:
    mode: str
    write_operations: list = field(default_factory=list)
    steps: list = field(default_factory=list)

# ---------------------------------------------------------------- 构建面接线
# 订单应用 spec → 有序构建计划（宿主执行，agent 不出写）。
# 铁律：
#   - GraphQL 写 op 必须经 op_entry() 解析成功（STATIC_CATALOG），解析不出 → 落 unknowns，不臆造。
#   - 微流程/页面/菜单的写 op 不在主 store bundle（lazy 子组件 / REST 端点），
#     channel=rest，证据走 skill LIVE 链（checkSchema→create 同 body；页面 base-info/create；
#     菜单 /udc/function），标注来源不冒称 bundle STATIC。
#   - body 只引用真实存在的构造器（metadata_artifacts / microflow.py / layout_model），不构造值。
#   - 部署上线=破坏性（ON_ONLINE）→ 标 DESTRUCTIVE，宿主须先确认。
#   - spec 未声明的对象（index/event/enum）绝不臆造生成，落 unknowns 提示扩展 spec。
_BUILD_EVIDENCE_LEVELS = ("STATIC_CATALOG", "LIVE_SMOKE", "OBSERVED_LIVE", "UNVERIFIED")


def _gql_op(op_name: str) -> dict | None:
    """GraphQL 写 op 解析：命中目录返回契约，未命中返回 None（调用方落 unknowns）。"""
    from components.udc.graphql_write_ops import op_entry
    return op_entry(op_name)


def _step(action: str, target: str, channel: str, op: str,
          body_builder: str | None = None, evidence: str = "UNVERIFIED",
          note: str = "", destructive: bool = False, unknowns: list | None = None,
          live_template: str | None = None) -> dict:
    s = {"action": action, "target": target, "channel": channel, "op": op,
         "evidence": evidence, "executed": False}
    if body_builder:
        s["body_builder"] = body_builder
    if live_template:
        # LIVE 已验证的写链模板（components.udc.live_write_templates.WRITE_TEMPLATES[key]）
        s["live_template"] = live_template
        s["evidence"] = "LIVE" if evidence in ("UNVERIFIED", "STATIC_CATALOG") else evidence
    if note:
        s["note"] = note
    if destructive:
        s["destructive"] = True
    if unknowns:
        s["unknowns"] = unknowns
    return s


class UdcPlanner:
    def plan(self, spec):
        steps = [{"action": "inspect_application", "target": spec.name}]
        for e in spec.entities:
            steps.append({"action": "inspect_entity", "target": e.name})
        for p in spec.pages:
            steps.append({"action": "inspect_page", "target": p.name})
        for m in spec.microflows:
            steps.append({"action": "inspect_microflow", "target": m.name})
        return {"mode": "dry-run", "write_operations": [], "steps": steps}

    def plan_application(self, spec):
        return UdcPlan("dry-run", [], [{"action": "inspect_application", "target": spec.name}])

    def plan_build(self, spec) -> dict:
        """订单应用构建计划：spec 声明的每个对象生成有序写操作契约。

        返回 dict（宿主据此逐步执行；agent 不出写）。
        每个 step：channel(graphql|rest) + op + body_builder 引用 + evidence 分级；
        未证项集中在 unknowns（op 解析失败 / spec 未声明但订单需求常见项）。
        """
        unknowns: list[str] = []
        steps: list[dict] = []
        write_ops: list[dict] = []
        seq = 0

        def add(step: dict) -> None:
            nonlocal seq
            step["seq"] = seq + 1
            seq += 1
            steps.append(step)
            write_ops.append(step)

        # ---- 应用级（GraphQL，STATIC_CATALOG）----
        app_op = _gql_op("udcApplicationPost")
        if app_op:
            add(_step("create_application", spec.name, "graphql", "udcApplicationPost",
                      body_builder="宿主组 body（应用名/编码/版型）", evidence="STATIC_CATALOG",
                      note=f"paramsType={app_op['paramsType']}, paramsKey={app_op['paramsKey']}"))
        else:
            unknowns.append("udcApplicationPost 未解析（catalog 缺失？），应用创建落 UNVERIFIED")

        # ---- 选项集（基础设置 UDC 枚举）：先建枚举本体，再批量建项（须在引用它的实体字段前）----
        for en in getattr(spec, "enums", []):
            enum_op = _gql_op("udcUdcEnumPost")
            if enum_op:
                add(_step("create_enum", en.name, "graphql", "udcUdcEnumPost",
                          body_builder="construction.metadata_artifacts.build_enum_body（appId/caption/name/orderNo）",
                          evidence="STATIC_CATALOG",
                          note="枚举本体；缺 orderNo 报 BOOT_1001（LIVE）"))
            else:
                unknowns.append(f"选项集 {en.name}: udcUdcEnumPost 未解析")
            if en.items:
                item_op = _gql_op("udcUdcEnumItemOperateBatchPost")
                if item_op:
                    add(_step("create_enum_items", en.name, "graphql",
                              "udcUdcEnumItemOperateBatchPost",
                              body_builder="construction.metadata_artifacts.build_enum_item_body（code 一律 int；name 大写字母+下划线）",
                              evidence="STATIC_CATALOG",
                              note=f"paramsType=[…]数组包装特例（§2.7.4）；{len(en.items)} 项"))
                else:
                    unknowns.append(f"选项集 {en.name} 项: udcUdcEnumItemOperateBatchPost 未解析")

        # ---- 每个实体：实体 → 逐字段属性 → 索引 → 事件 → 参照（顺序依赖：本体先建）----
        for e in spec.entities:
            ent_op = _gql_op("udcEntityPost")
            if ent_op:
                note_extra = ""
                if getattr(e, "stereotype", ""):
                    note_extra += f"；版型={e.stereotype}"
                if getattr(e, "parent_entity", ""):
                    note_extra += f"；父实体={e.parent_entity}"
                if getattr(e, "attribute_set", ""):
                    note_extra += f"；字段集={e.attribute_set}"
                add(_step("create_entity", e.name, "graphql", "udcEntityPost",
                          body_builder="宿主组 body（caption/编码/版型/字段集/父实体）",
                          evidence="STATIC_CATALOG",
                          live_template="entity_create",
                          note=f"paramsType={ent_op['paramsType']}, appId 由 redux 注入（§2.7.1）{note_extra}；"
                               "LIVE 实证：standard 版型+MAIN type 最小 body 即可，自动生成 9 预置字段"))
            else:
                unknowns.append(f"实体 {e.name}: udcEntityPost 未解析")
            for f in e.fields:
                attr_op = _gql_op("udcEntityAttributePost")
                attr_note = f"dataType={f.type}"
                if f.type == "ENTITY" and (f.multi_select or f.reference):
                    attr_note += "；多选/参照须 ENTITY+relationType+relationEntity+multiSelect"
                if f.enum_name:
                    attr_note += f"；枚举引用选项集={f.enum_name}"
                if f.default_value:
                    attr_note += "；默认值六件套进 plan_only（create 面受键 UNVERIFIED，不擅自进 body）"
                if attr_op:
                    add(_step("create_attribute", f"{e.name}.{f.name}", "graphql",
                              "udcEntityAttributePost",
                              body_builder="attribute_semantics.build_attribute_plan",
                              evidence="STATIC_CATALOG", note=attr_note))
                else:
                    unknowns.append(f"实体 {e.name} 字段 {f.name}: udcEntityAttributePost 未解析")
            # 索引（§2.8.3①：idx_/uk_ 前缀、fieldIds≤5 逗号分隔、非自建/已发布禁改）
            for ix in getattr(e, "indexes", []):
                ix_op = _gql_op("udcIndexPost")
                if not ix.fields:
                    unknowns.append(f"实体 {e.name} 索引 {ix.caption}: 无 fields，不生成")
                    continue
                if len(ix.fields) > 5:
                    unknowns.append(f"实体 {e.name} 索引 {ix.caption}: {len(ix.fields)} 字段超上限 5（INDEX_FIELD_MAX）")
                if ix_op:
                    add(_step("create_index", f"{e.name}.{ix.caption}", "graphql", "udcIndexPost",
                              body_builder="construction.metadata_artifacts.build_index_body（fieldIds 逗号分隔字符串，给数组报 BOOT_3002）",
                              evidence="STATIC_CATALOG",
                              note=f"前缀 {'uk_' if ix.type == 'UNIQUE' else 'idx_'}；fields={ix.fields}"))
                else:
                    unknowns.append(f"实体 {e.name} 索引 {ix.caption}: udcIndexPost 未解析")
            # 事件（§2.8.2① 坐实：事件 tab「新建事件」实际走 createEventWithData→
            # udcEventCreateWithDataPost，携带 eventDataList 由微流程节点输出参数构造；
            # udcEventPost 是基础事件形态，非 tab 主链）
            for ev in getattr(e, "events", []):
                ev_op = _gql_op("udcEventCreateWithDataPost")
                if ev.trigger.upper() not in ("BUSINESS_EVENT", "MANUAL", "SCHEDULE"):
                    unknowns.append(f"实体 {e.name} 事件 {ev.name}: trigger={ev.trigger!r} 不在值域，不臆造")
                if ev_op:
                    add(_step("create_event", f"{e.name}.{ev.name}", "graphql",
                              "udcEventCreateWithDataPost",
                              body_builder="construction.metadata_artifacts.build_event_with_data_body"
                                           "（§2.8.2①：source=MICRO_FLOW/sourceId=实体id/eventDataList 由微流程节点输出参数构造）",
                              evidence="STATIC_CATALOG",
                              note=f"trigger={ev.trigger}；eventDataList.attributes 来自微流程节点输出参数"
                                   "（outputName/description/dataType/javaType/type），Dto/Enum 取 javaType"))
                else:
                    unknowns.append(f"实体 {e.name} 事件 {ev.name}: udcEventCreateWithDataPost 未解析")
            # 参照（§2.8.3③ 提交链：有 id 走 UpdateConfigInfo，无 id 走 CreateConfigInfo）
            for rf in getattr(e, "refer", []):
                op_name = "udcReferConfigUpdateConfigInfoPost" if rf.id else "udcReferConfigCreateConfigInfoPost"
                rf_op = _gql_op(op_name)
                if rf_op:
                    add(_step("create_refer" if not rf.id else "update_refer",
                              f"{e.name}.{rf.caption}", "graphql", op_name,
                              body_builder="construction.metadata_artifacts.build_refer_config_body"
                                           "（module-53993.js:614-667 e1() 逐字：顶层 appId/entityId/caption/type/id"
                                           "+ referConfigDetail[PC(,MOBILE)]，每 detail configInfo=JSON.stringify(config)）",
                              evidence="STATIC_CATALOG",
                              note=f"terminal={rf.terminal}；有 id={rf.id!r} 走更新否则新建；"
                                   "refer_type 字面值 List/TreeList/LeftTreeRightList（module-75586）"))
                else:
                    unknowns.append(f"实体 {e.name} 参照 {rf.caption}: {op_name} 未解析")
            # 开放 API / 数据权限（udc_entity.permission / open_api_data；开关面非独立 op）
            if getattr(e, "data_permission", False):
                unknowns.append(f"实体 {e.name}: 数据权限开关（udc_entity.permission）为运行态列，"
                                "设计态不单独生成，宿主建实体时随 body 置位")

        # ---- 每个微流程：checkSchema → create（REST，skill LIVE 证据链）----
        for m in spec.microflows:
            if m.trigger.upper() not in ("BUSINESS_EVENT", "MANUAL", "SCHEDULE"):
                unknowns.append(f"微流程 {m.name}: trigger={m.trigger!r} 不在 REST 字符串枚举值域"
                                f"（BUSINESS_EVENT/MANUAL/SCHEDULE），非法值不臆造")
            mf_note = "create 前必过 checkSchema；content.check=true 且 errors=0 才创建"
            if getattr(m, "group_type", ""):
                mf_note += f"；实体规则组={m.group_type}（VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE）"
            if getattr(m, "source_id", ""):
                mf_note += f"；sourceId={m.source_id}"
            add(_step("microflow_check_schema", m.name, "rest",
                      "POST /service/udc/microflow/checkSchema",
                      body_builder="construction.microflow.build_microflow_create_body + check_schema_body",
                      evidence="LIVE_SMOKE", note=mf_note))
            add(_step("microflow_create", m.name, "rest",
                      "POST /udc/microflow/create",
                      body_builder="construction.microflow.build_microflow_create_body（dataSchema=json.dumps 字符串）",
                      evidence="LIVE_SMOKE",
                      live_template="microflow_create",
                      note="LIVE 实证：GraphQL udcMicroflowCreatePost 空基座（nodes=[]/triggerType=MANUAL）直接创建成功（DRAFT）；"
                           "update 走 udcMicroflowUpdatePost 回传全量 DTO；dataSchema 是 JSON 字符串非嵌套对象"))

        # ---- 每个页面：基础 + 菜单 + 规则/面板/工具栏/详情/列宽 + 微流程绑定（REST，LIVE 证据链）----
        for p in spec.pages:
            add(_step("page_create_base", p.name, "rest",
                      "POST /udc/page-info/base-info/create",
                      body_builder="live_write_templates.WRITE_TEMPLATES['page_create']（PageDefinitionDto：curTerminalType+pageItems[].urlType/menuId）",
                      evidence="LIVE",
                      live_template="page_create",
                      note=f"LIVE 实证（datamigration）：必须先建菜单（pageItems[].menuId），"
                           f"真实路径带 page-info 前缀；page_type={p.page_type or 'SEARCH_LIST'}"
                            + (f"；列宽 {len(p.columns)} 项" if p.columns else "")))
            add(_step("page_menu_create", p.name, "rest",
                      "POST /udc/function",
                      body_builder="function_node_model.FUNCTION_ENDPOINTS['create']",
                      evidence="OBSERVED_LIVE",
                      live_template="menu_create",
                      note="菜单节点；LIVE 实证走 GraphQL udcFunctionPost（REST /udc/function 是另一入口）；宿主把 spec.menus 里 refer_page 指向本页的项挂上"))
            if getattr(p, "page_rules", []):
                add(_step("page_rules_create", p.name, "rest",
                          "POST /service/udc/udc-runtime/filter-plan/create-new（页面规则弹窗）",
                          body_builder="construction.metadata_artifacts.build_filter_plan_body"
                                       "（LIVE REST 写面：planType 数字码 0=FILTER隐藏/2=LIST可见）",
                          evidence="OBSERVED_LIVE",
                          note=f"{len(p.page_rules)} 条页面规则；sourceId=<{{page_id}}>_udcDataGridView_<{{suffix}}> 须宿主回填真实 id；"
                               "设计器前端另走 GraphQL udcUdcRuntimeFilterPlanPost（bundle 51796）两者并存"))
            if getattr(p, "panels", []):
                add(_step("page_panels_bind", p.name, "rest",
                          "POST /udc/page-layout/update（面板与打开面板动作）",
                          body_builder="layout_model.LAYOUT_ENDPOINTS['update']",
                          evidence="OBSERVED_LIVE",
                          note=f"{len(p.panels)} 个面板；组件事件绑定在宿主构建期补齐"))
            if getattr(p, "toolbar", []):
                add(_step("page_toolbar_bind", p.name, "rest",
                          "POST /udc/page-info/update-draf（工具栏按钮/测试按钮位）",
                          body_builder="layout_model.LAYOUT_ENDPOINTS['update_draft']",
                          evidence="LIVE",
                          live_template="page_schema_draft",
                          note=f"工具栏 {p.toolbar}；LIVE 实证 update-draf 收 draftPageSchema（children+childById 组件树），"
                               "schemaState EMPTY→DRAFT；测试按钮位须在宿主页面点击验证等价"))
            add(_step("page_schema_formal", p.name, "rest",
                      "POST /udc/page-info/update（页面 schema 正式保存）",
                      body_builder="live_write_templates.WRITE_TEMPLATES['page_schema_formal']"
                                   "（真绑实体三要素 + 业务列剔除系统字段 + 行按钮/事件绑定）",
                      evidence="LIVE",
                      live_template="page_schema_formal",
                      note="LIVE 实证：①业务列剔除 9 系统字段（成熟页 13 列零系统字段）；"
                           "②行按钮=uiModel.controlledProps（查看/编辑/删除）+flowAuthKeys；"
                           "③事件=events[]（buildin/openPage DETAIL view|edit、widget/ENTITY_DELETE）；"
                           "④update 与 update-draf body 同构；回读 schemaState=FORMAL"))
            if getattr(p, "detail", {}):
                add(_step("page_detail_bind", p.name, "rest",
                          "POST /udc/page-layout/update（编辑穿透详情/详情排版）",
                          body_builder="layout_model.LAYOUT_ENDPOINTS['update']",
                          evidence="OBSERVED_LIVE",
                          note=f"详情面 {list(p.detail.keys())}；穿透详情绑定宿主补"))
            if getattr(p, "bind_microflow", ""):
                add(_step("page_bind_microflow", p.name, "rest",
                          "POST /udc/function/create/function-refer（页面↔微流程绑定）",
                          body_builder="function_node_model.FUNCTION_ENDPOINTS['create_page_refer']",
                          evidence="OBSERVED_LIVE",
                          note=f"绑定微流程={p.bind_microflow}"))

        # ---- Excel 导入/导出模板与数据（ctp_excel_export_template；副作用显式分类）----
        for x in getattr(spec, "excel", []):
            add(_step(f"excel_{x.direction}", x.entity, "rest",
                      f"POST /service/udc/excel/{x.direction}"
                      + ("（check-excel 有副作用，不得进只读白名单）" if x.direction == "export" and not x.template_id else ""),
                      body_builder="excel_model.ExcelTemplateModel（app_id 是 String！双列结构 metadataContent+excelHeadInfo 缺一=列映射不完整）",
                      evidence="OBSERVED_LIVE",
                      note=f"direction={x.direction}；异步 redisKey 只是句柄，验收须到文件/行结果层"))

        # ---- 菜单（应用级 function tree 节点；spec.menus 未声明则宿主在页面绑定期补）----
        for mn in getattr(spec, "menus", []):
            add(_step("menu_create", mn.caption, "rest",
                      "POST /udc/function（function tree 节点）",
                      body_builder="function_node_model.FUNCTION_ENDPOINTS['create']",
                      evidence="OBSERVED_LIVE",
                      note=f"挂页面={mn.page or '未指定'}；terminal={mn.terminal}；order={mn.order_no}"))

        # ---- 部署上线（破坏性，宿主须先确认）----
        add(_step("deploy_online", spec.name, "rest",
                  "POST /udc/deployment/...（deploy_chain_model.DEPLOY_OPS）",
                  body_builder="deploy_chain_model（udcDeploymentAppOnlineNewPost deployType=ON_ONLINE）",
                  evidence="STATIC_CATALOG", destructive=True,
                  note="破坏性：上线后版本锁定，须宿主显式确认再执行"))

        return {
            "mode": "build-plan",
            "spec": spec.to_dict() if hasattr(spec, "to_dict") else spec,
            "steps": steps,
            "write_operations": [
                {"op": s["op"], "channel": s["channel"], "evidence": s["evidence"],
                 "seq": s["seq"]} for s in write_ops],
            "unknowns": unknowns,
            "evidence_levels": list(_BUILD_EVIDENCE_LEVELS),
            "executed": False,
            "writes_performed": False,
            "discipline": "agent 只出计划不出写；破坏性步骤(Deploy)宿主须先确认；"
                          "op 解析失败/spec 未声明项落 unknowns 不臆造",
        }
