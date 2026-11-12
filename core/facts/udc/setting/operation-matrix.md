# 设置域 · 操作存在性矩阵（update / delete / search）

> 证据等级：**LIVE**（test2，2026-10-23，空 body 探测 + 错误码判别）
> 探针：`tools/core/setting/probe_setting_ops.py`
> 目的：把「端点存在，未实测」这类 UNVERIFIED 落成确定结论（存在 / 不存在），
> 而不是让下一个人再摸一遍。

## 零、为什么单独建这一格

设置域 9 个 tab 的事实格里散着 47 条 `UNVERIFIED`，其中很大一部分是同一个形态：

```
| `delete` | **UNVERIFIED** | 端点存在，未实测 |
```

「端点存在」和「参数怎么传」是两件事。前者能一次全测完，后者要逐个建样本。
先把前者收口，后面推进才不用重复摸路。

## 一、判定方法（三处必须做对，否则结论全错）

```
① GraphQL 的 code 嵌在 data.data0.code，不是顶层
   看顶层 r.get("code") 会永远拿不到 → 全部误判成"未定"
② 字段集 / 二维码 / 导入导出模板走 REST，不是 GraphQL
   用 GraphQL 探它们必然 FieldUndefined —— 那是**假阴性**，不代表不存在
③ 不能写 str(r.get("message"))[:60] 再判真假
   str(None) == "None" 为真 → 会把"什么都没返回"误判成"存在"
```

判别口径：

```
GraphQL   data.data0.code 是非空字符串        → 存在
          FieldUndefined                      → 不存在（VACUUM）
REST      HTTP 404 / server_404               → 不存在
          HTTP 405                            → 存在但方法不对
          其它（含业务错误码）                 → 存在
```

★ **空 body 返回业务错误码本身就是"存在"的正证据**：参数校验跑到了才报必填缺失。
只有 FieldUndefined / 404 才算不存在。

## 二、GraphQL 通道：14/14 全部存在

| 域 | operation | 空 body 返回 |
|---|---|---|
| 选项集 | `udcUdcEnumUpdatePost` | `BOOT_1001` 应用ID 不能为null; 选项集名称 不能为空 |
| 选项集 | `udcUdcEnumItemUpdatePost` | `BOOT_1001` 选项名称 不能为空; 选项值 不能为null |
| 选项集 | `udcUdcEnumItemDeletePost` | **`BOOT_0000` SUCCESS** ⚠ 成功码不可信 |
| 选项集 | `udcUdcEnumBatchDeletePost` | **`BOOT_0000` SUCCESS** ⚠ 同上 |
| 选项集 | `udcUdcEnumCategoryDeletePost` | **`BOOT_0000` SUCCESS** ⚠ 同上 |
| 选项集 | `udcUdcEnumCategoryUpdatePost` | `BOOT_1001` 应用ID 不能为null; 分类名称 不能为空 |
| 参数 | `udcCtpParameterDefinitonDeletePost` | **`BOOT_0000` SUCCESS** ⚠ 同上 |
| 参数 | `udcCtpParameterDefinitonSearch` | `BOOT_3000`（参数形态不对） |
| 参数 | `udcCtpParameterDefinitonUpdatePost` | `BOOT_1001` 参数显示名称 不能为空 |
| 流水号 | `udcSerialSchemeUpdatePost` | `UDC_APP_0001` 应用不存在 |
| 流水号 | `udcSerialSchemeDeletePost` | `BOOT_4002` 数据不存在或无权限查看 |
| 自定义对象 | `udcDataTransferObjectUpdateDtoPost` | `BOOT_1001` 应用Id 不能为null; 对象显示名称 不能为空 |
| 扩展实体 | `udcScalabilityDeletePost` | `BOOT_3000`（参数形态不对） |
| 扩展实体 | `udcScalabilityOptionUpdatePost` | `BOOT_1001` appId 不能为null; 方案名称 不能为空 |

⚠ **六个 delete 在空 body 下回 `BOOT_0000`** —— 这是本域最危险的假成功信号。
判据永远是回读：删前记录行，删后 `SELECT ... WHERE id=<id>` 必须空。

## 三、REST 通道：10 存在 / 1 不存在

| 域 | path | 判定 | 依据 |
|---|---|---|---|
| 字段集 | `POST /service/udc/attributeSet/delete` | 存在 | `UDC_ENTITY_0022` 字段集不存在 |
| 字段集 | `POST /service/udc/attributeSet/update` | 存在 | `BOOT_1001` 字段集所属应用Id 不能为null |
| 字段集 | `POST /service/udc/attributeSet/search-list` | 存在 | `BOOT_0000` SUCCESS（需 pageInfo） |
| 字段集 | `POST /service/udc/attributeSet/search/term` | 存在 | `BOOT_1001` request 调用异常,第2个参数为null |
| 二维码 | `POST /service/udc/qrcode-rule/update` | 存在 | `BOOT_1001` UDC应用GUID 不能为null |
| 二维码 | `POST /service/udc/qrcode-rule/delete` | 存在 | `BOOT_4002` 数据不存在或无权限查看 |
| 二维码 | `POST /service/udc/qrcode-rule/search` | 存在 | `BOOT_3000`（参数形态不对） |
| 导入导出模板 | `POST /service/udc/excel/update-template` | 存在 | `BOOT_4002` 数据不存在或无权限查看 |
| 导入导出模板 | **`POST /service/udc/excel/delete-template`** | **不存在** | **HTTP 404** |
| 导入导出模板 | `POST /service/udc/excel/export-excel-template` | 存在 | `BOOT_1001` 模板Id 不能为null |
| 导入导出模板 | `POST /service/udc/excel/search` | 存在 | `BOOT_3000`（参数形态不对） |

### ★ 导入导出模板没有 delete-template

`/service/udc/excel/delete-template` 是 **404**，不是参数问题。要删模板得走别的通道
（候选：GraphQL `ctpExcelExportTemplateDelete*` 族，或模板自身的 update 置失效状态）。
**当前状态 VACUUM（该路径确实不存在）；模板删除能力整体仍是 UNVERIFIED。**

## 四、结论怎么用

| 原来的写法 | 现在可以写 |
|---|---|
| `delete` **UNVERIFIED**（端点存在，未实测） | `delete` **端点已确认存在**（LIVE 2026-10-23），参数未实发 |
| `update` **UNVERIFIED** | 同上 |
| 模板删除 | **VACUUM**（`/excel/delete-template` 404）；替代通道 UNVERIFIED |

⚠ 这是**端点存在性**，不是**能力可用性**。报「某能力打通」仍须：
真实参数实发 → DB 回读 → （涉及页面时）渲染确认。

## 五、未覆盖

本轮只探了上表这些名字。以下候选**未探**（避免穷举浪费）：

```
字段集的其他 REST 变体（update-fieldcode 之类）
二维码 update-fieldcode / update-implement
Excel 模板的 GraphQL 删除族
选项集分组 Update 的必填槽位
```

需要时按同一方法（GraphQL 看 `data.data0.code`、REST 看 404、不用 str(None) 判真假）补探。
