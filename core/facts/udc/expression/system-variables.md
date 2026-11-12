# 表达式系统变量目录（131 项 / 4 组）

> 证据等级：**LIVE**（`POST /service/udc/expression/preset/list`，
> `terminalSupportType=BACKEND`，test2，2026-10-23 完整原文）
> 原文：用户提供的完整响应（3989 行 / 204KB），本文件由
> `tools/core/expression/parse_preset_full.py` 生成，勿手改。
>
> ★ 系统变量与 `terminalSupportType` **无关**：BACKEND / FRONTEND / ALL 三档都是 131 项。
>   只有函数面被裁剪（88 / 81）。
>
> ★ 两条解析通路不等价（既有事实）：
>   `name` 全名（`system.currentDateTime`）取其 `resultType`；
>   短名（`functionName`）只要同名于某函数就被当函数调用、取函数返回类型。
>   需要稳定类型时用 `name`，别用短名。

## 总览

| 分组 | 名称 | 数量 |
|---|---|---|
| organization | 组织机构 | 95 |
| date | 日期 | 33 |
| env | 环境变量 | 2 |
| plugin | 插件 | 1 |

## resultType 分布

| 类型 | 数量 |
|---|---|
| ARRAY | 63 |
| STRING | 25 |
| DATE | 25 |
| BIGINTEGER | 11 |
| INTEGER | 4 |
| DATETIME | 1 |
| TIME | 1 |
| BOOLEAN | 1 |

---

## organization（组织机构）— 95 项

| 全名 | 说明 | 短名 | 结果类型 | 关联实体 | hidden |
|---|---|---|---|---|---|
| `system.currentUserId` | 登录人员ID | `currentUserId` | BIGINTEGER | OrgMember |  |
| `system.currentUserName` | 登录人员姓名 | `currentUserName` | STRING | - |  |
| `system.currentUserCode` | 登录人员编号 | `currentUserCode` | STRING | - |  |
| `system.currentUserLoginName` | 登录人员的用户名 | `currentUserLoginName` | STRING | - |  |
| `system.currentOrgId` | 登录部门ID | `currentOrgId` | BIGINTEGER | OrgUnit |  |
| `system.currentOrgName` | 登录人员所在部门名称 | `currentOrgName` | STRING | - |  |
| `system.currentOrgCode` | 登录人员所在部门编号 | `currentOrgCode` | STRING | - |  |
| `system.currentPostId` | 登录人员主岗岗位ID | `currentPostId` | BIGINTEGER | OrgPost |  |
| `system.currentPostName` | 登录人员主岗岗位名称 | `currentPostName` | STRING | - |  |
| `system.currentPostCode` | 登录人员主岗岗位编号 | `currentPostCode` | STRING | - |  |
| `system.currentPostIds` | 登录人员任职岗位ID | `currentPostIds` | ARRAY | OrgPost |  |
| `system.currentPostNames` | 登录人员任职岗位名称 | `currentPostNames` | ARRAY | - |  |
| `system.currentPostCodes` | 登录人员任职岗位编码 | `currentPostCodes` | ARRAY | - |  |
| `system.currentPartTimePostIds` | 登录人员兼职岗位ID | `currentPartTimePostIds` | ARRAY | OrgPost |  |
| `system.currentPartTimePostNames` | 登录人员兼职岗位名称 | `currentPartTimePostNames` | ARRAY | - |  |
| `system.currentPartTimePostCodes` | 登录人员兼职岗位编码 | `currentPartTimePostCodes` | ARRAY | - |  |
| `system.currentMemberOrgRoleIds` | 登录人员组织角色ID | `currentMemberOrgRoleIds` | ARRAY | - |  |
| `system.currentMemberOrgRoleCodes` | 登录人员组织角色编码 | `currentMemberOrgRoleCodes` | ARRAY | - |  |
| `system.currentJobId` | 登录职务ID | `currentJobId` | BIGINTEGER | OrgJob |  |
| `system.currentJobName` | 登录人员职务名称 | `currentJobName` | STRING | - |  |
| `system.currentJobCode` | 登录人员职务编号 | `currentJobCode` | STRING | - |  |
| `system.currentLevelId` | 登录职级ID | `currentLevelId` | BIGINTEGER | OrgLevel |  |
| `system.currentLevelName` | 登录人员职级名称 | `currentLevelName` | STRING | - |  |
| `system.currentLevelCode` | 登录人员职级编号 | `currentLevelCode` | STRING | - |  |
| `system.currentInstitutionId` | 登录人员机构ID | `currentInstitutionId` | BIGINTEGER | OrgUnit |  |
| `system.currentInstitutionName` | 登录人员所在机构名称 | `currentInstitutionName` | STRING | - |  |
| `system.currentInstitutionCode` | 登录人员所在机构编号 | `currentInstitutionCode` | STRING | - |  |
| `system.currentInstitutionLogo` | 登录人员所在机构Logo | `currentInstitutionLogo` | STRING | - |  |
| `system.currentAllParentOrgId` | 登录人员所有上级机构ID | `currentAllParentOrgId` | ARRAY | - |  |
| `system.currentAllParentOrgCode` | 登录人员所有上级机构编号 | `currentAllParentOrgCode` | ARRAY | - |  |
| `system.currentAllParentOrgName` | 登录人员所有上级机构名称 | `currentAllParentOrgName` | ARRAY | - |  |
| `system.currentParentOrgId` | 登录人员上级部门ID | `currentParentOrgId` | BIGINTEGER | OrgUnit |  |
| `system.currentParentOrgName` | 登录人员上级部门名称 | `currentParentOrgName` | STRING | - |  |
| `system.currentParentOrgCode` | 登录人员上级部门编号 | `currentParentOrgCode` | STRING | - |  |
| `system.currentFirstLevelOrgId` | 登录人员所在一级部门ID | `currentFirstLevelOrgId` | BIGINTEGER | OrgUnit |  |
| `system.currentFirstLevelOrgName` | 登录人员所在一级部门名称 | `currentFirstLevelOrgName` | STRING | - |  |
| `system.currentFirstLevelOrgCode` | 登录人员所在一级部门编号 | `currentFirstLevelOrgCode` | STRING | - |  |
| `system.currentMemberPostOrgIds` | 登录人员任职各部门ID | `currentMemberPostOrgIds` | ARRAY | OrgUnit |  |
| `system.currentParentInstitutionIds` | 登录人员上一级机构ID | `currentParentInstitutionIds` | ARRAY | OrgUnit |  |
| `system.currentParentInstitutionNames` | 登录人员上一级机构名称 | `currentParentInstitutionNames` | ARRAY | OrgUnit |  |
| `system.currentParentInstitutionCodes` | 登录人员上一级机构编号 | `currentParentInstitutionCodes` | ARRAY | OrgUnit |  |
| `system.currentMemberPostOrgNames` | 登录人员任职各部门名称 | `currentMemberPostOrgNames` | ARRAY | - |  |
| `system.currentMemberPostOrgCodes` | 登录人员任职各部门编号 | `currentMemberPostOrgCodes` | ARRAY | - |  |
| `system.currentMemberPostPartTimeOrgIds` | 登录人员兼职各部门ID | `currentMemberPostPartTimeOrgIds` | ARRAY | OrgUnit |  |
| `system.currentMemberPostPartTimeOrgNames` | 登录人员兼职各部门名称 | `currentMemberPostPartTimeOrgNames` | ARRAY | - |  |
| `system.currentMemberPostPartTimeOrgCodes` | 登录人员兼职各部门编号 | `currentMemberPostPartTimeOrgCodes` | ARRAY | - |  |
| `system.currentMemberPostInstitutionIds` | 登录人员任职各机构ID | `currentMemberPostInstitutionIds` | ARRAY | OrgUnit |  |
| `system.currentMemberPostInstitutionNames` | 登录人员任职各机构名称 | `currentMemberPostInstitutionNames` | ARRAY | - |  |
| `system.currentMemberPostInstitutionCodes` | 登录人员任职各机构编号 | `currentMemberPostInstitutionCodes` | ARRAY | - |  |
| `system.currentMemberPostPartTimeInstitutionIds` | 登录人员兼职各机构ID | `currentMemberPostPartTimeInstitutionIds` | ARRAY | OrgUnit |  |
| `system.currentMemberPostPartTimeInstitutionNames` | 登录人员兼职各机构名称 | `currentMemberPostPartTimeInstitutionNames` | ARRAY | - |  |
| `system.currentMemberPostPartTimeInstitutionCodes` | 登录人员兼职各机构编号 | `currentMemberPostPartTimeInstitutionCodes` | ARRAY | - |  |
| `system.currentManagerDepartmentIds` | 登录人员负责的各部门ID | `currentManagerDepartmentIds` | ARRAY | OrgUnit |  |
| `system.currentManagerDepartmentNames` | 登录人员负责的各部门名称 | `currentManagerDepartmentNames` | ARRAY | - |  |
| `system.currentManagerDepartmentCodes` | 登录人员负责的各部门编号 | `currentManagerDepartmentCodes` | ARRAY | - |  |
| `system.currentManagerInstitutionIds` | 登录人员负责的各机构ID | `currentManagerInstitutionIds` | ARRAY | OrgUnit |  |
| `system.currentManagerInstitutionNames` | 登录人员负责的各机构名称 | `currentManagerInstitutionNames` | ARRAY | - |  |
| `system.currentManagerInstitutionCodes` | 登录人员负责的各机构编号 | `currentManagerInstitutionCodes` | ARRAY | - |  |
| `system.currentLeaderDepartmentIds` | 登录人员分管的各部门ID | `currentLeaderDepartmentIds` | ARRAY | OrgUnit |  |
| `system.currentLeaderDepartmentNames` | 登录人员分管的各部门名称 | `currentLeaderDepartmentNames` | ARRAY | - |  |
| `system.currentLeaderDepartmentCodes` | 登录人员分管的各部门编号 | `currentLeaderDepartmentCodes` | ARRAY | - |  |
| `system.currentLeaderInstitutionIds` | 登录人员分管的各机构ID | `currentLeaderInstitutionIds` | ARRAY | OrgUnit |  |
| `system.currentLeaderInstitutionNames` | 登录人员分管的各机构名称 | `currentLeaderInstitutionNames` | ARRAY | - |  |
| `system.currentLeaderInstitutionCodes` | 登录人员分管的各机构编号 | `currentLeaderInstitutionCodes` | ARRAY | - |  |
| `system.currentLegalOrgId` | 登录人员法人组织ID | `currentLegalOrgId` | BIGINTEGER | OrgUnit |  |
| `system.rootInstitutionId` | 根机构ID | `rootInstitutionId` | BIGINTEGER | OrgUnit |  |
| `system.rootInstitutionName` | 根机构名称 | `rootInstitutionName` | STRING | - |  |
| `system.rootInstitutionCode` | 根机构编号 | `rootInstitutionCode` | STRING | - |  |
| `system.currentUserType` | 登录用户类型 | `currentUserType` | STRING | - |  |
| `system.currentSecretLevel` | 登录人员可见资源的最高密级 | `currentSecretLevel` | INTEGER | - |  |
| `system.currentSecretLevelId` | 登录人员可见资源的最高密级ID | `currentSecretLevelId` | BIGINTEGER | - |  |
| `system.currentMultiOrgId` | 登录人员所在多维组织ID | `currentMultiOrgId` | ARRAY | - |  |
| `system.currentMultiOrgCode` | 登录人员所在多维组织编号 | `currentMultiOrgCode` | ARRAY | - |  |
| `system.currentMultiOrgName` | 登录人员所在多维组织名称 | `currentMultiOrgName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentId` | 登录人员所在多维组织部门ID | `currentMultiOrgDepartmentId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentCode` | 登录人员所在多维组织部门编号 | `currentMultiOrgDepartmentCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentName` | 登录人员所在多维组织部门名称 | `currentMultiOrgDepartmentName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentParentId` | 登录人员所在多维组织部门上级ID | `currentMultiOrgDepartmentParentId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentParentCode` | 登录人员所在多维组织部门上级编号 | `currentMultiOrgDepartmentParentCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentParentName` | 登录人员所在多维组织部门上级名称 | `currentMultiOrgDepartmentParentName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentFirstId` | 登录人员所在多维组织部门一级ID | `currentMultiOrgDepartmentFirstId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentFirstCode` | 登录人员所在多维组织部门一级编号 | `currentMultiOrgDepartmentFirstCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentFirstName` | 登录人员所在多维组织部门一级名称 | `currentMultiOrgDepartmentFirstName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleId` | 登录人员负责的多维组织ID | `currentMultiOrgDepartmentResponsibleId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleCode` | 登录人员负责的多维组织编号 | `currentMultiOrgDepartmentResponsibleCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleName` | 登录人员负责的多维组织名称 | `currentMultiOrgDepartmentResponsibleName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideId` | 登录人员分管的多维组织ID | `currentMultiOrgDepartmentDivideId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideCode` | 登录人员分管的多维组织编号 | `currentMultiOrgDepartmentDivideCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideName` | 登录人员分管的多维组织名称 | `currentMultiOrgDepartmentDivideName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleDepartmentId` | 登录人员负责的多维组织部门ID | `currentMultiOrgDepartmentResponsibleDepartmentId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleDepartmentCode` | 登录人员负责的多维组织部门编号 | `currentMultiOrgDepartmentResponsibleDepartmentCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentResponsibleDepartmentName` | 登录人员负责的多维组织部门名称 | `currentMultiOrgDepartmentResponsibleDepartmentName` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideDepartmentId` | 登录人员分管的多维组织部门ID | `currentMultiOrgDepartmentDivideDepartmentId` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideDepartmentCode` | 登录人员分管的多维组织部门编号 | `currentMultiOrgDepartmentDivideDepartmentCode` | ARRAY | - |  |
| `system.currentMultiOrgDepartmentDivideDepartmentName` | 登录人员分管的多维组织部门名称 | `currentMultiOrgDepartmentDivideDepartmentName` | ARRAY | - |  |

## date（日期）— 33 项

| 全名 | 说明 | 短名 | 结果类型 | 关联实体 | hidden |
|---|---|---|---|---|---|
| `system.currentDate` | 系统日期 | `currentDate` | DATE | - |  |
| `system.currentDateTime` | 系统日期时间 | `currentDateTime` | DATETIME | - |  |
| `system.currentTime` | 系统时间 | `currentTime` | TIME | - |  |
| `system.firstDay4ThisWeek` | 本周初日期 | `firstDay4ThisWeek` | DATE | - |  |
| `system.lastDay4ThisWeek` | 本周末日期 | `lastDay4ThisWeek` | DATE | - |  |
| `system.firstDay4ThisMonth` | 本月初日期 | `firstDay4ThisMonth` | DATE | - |  |
| `system.lastDay4ThisMonth` | 本月末日期 | `lastDay4ThisMonth` | DATE | - |  |
| `system.firstDay4ThisSeason` | 本季度初日期 | `firstDay4ThisSeason` | DATE | - |  |
| `system.lastDay4ThisSeason` | 本季度末日期 | `lastDay4ThisSeason` | DATE | - |  |
| `system.firstDay4ThisYear` | 本年初日期 | `firstDay4ThisYear` | DATE | - |  |
| `system.lastDay4ThisYear` | 本年末日期 | `lastDay4ThisYear` | DATE | - |  |
| `system.firstDay4PreviousWeek` | 上周初日期 | `firstDay4PreviousWeek` | DATE | - |  |
| `system.lastDay4PreviousWeek` | 上周末日期 | `lastDay4PreviousWeek` | DATE | - |  |
| `system.firstDay4PreviousMonth` | 上月初日期 | `firstDay4PreviousMonth` | DATE | - |  |
| `system.lastDay4PreviousMonth` | 上月末日期 | `lastDay4PreviousMonth` | DATE | - |  |
| `system.firstDay4PreviousSeason` | 上季度初日期 | `firstDay4PreviousSeason` | DATE | - |  |
| `system.lastDay4PreviousSeason` | 上季度末日期 | `lastDay4PreviousSeason` | DATE | - |  |
| `system.firstDay4PreviousYear` | 上年初日期 | `firstDay4PreviousYear` | DATE | - |  |
| `system.lastDay4PreviousYear` | 上年末日期 | `lastDay4PreviousYear` | DATE | - |  |
| `system.firstDay4NextWeek` | 下周初日期 | `firstDay4NextWeek` | DATE | - |  |
| `system.lastDay4NextWeek` | 下周末日期 | `lastDay4NextWeek` | DATE | - |  |
| `system.firstDay4NextMonth` | 下月初日期 | `firstDay4NextMonth` | DATE | - |  |
| `system.lastDay4NextMonth` | 下月末日期 | `lastDay4NextMonth` | DATE | - |  |
| `system.firstDay4NextSeason` | 下季度初日期 | `firstDay4NextSeason` | DATE | - |  |
| `system.lastDay4NextSeason` | 下季度末日期 | `lastDay4NextSeason` | DATE | - |  |
| `system.firstDay4NextYear` | 下年初日期 | `firstDay4NextYear` | DATE | - |  |
| `system.lastDay4NextYear` | 下年末日期 | `lastDay4NextYear` | DATE | - |  |
| `system.currentDay` | 本日 | `currentDay` | STRING | - |  |
| `system.tomorrow` | 明日 | `tomorrow` | STRING | - |  |
| `system.yesterday` | 昨日 | `yesterday` | STRING | - |  |
| `system.currentYear` | 本年 | `currentYear` | INTEGER | - |  |
| `system.currentSeason` | 本季 | `currentSeason` | INTEGER | - |  |
| `system.currentMonth` | 本月 | `currentMonth` | INTEGER | - |  |

## env（环境变量）— 2 项

| 全名 | 说明 | 短名 | 结果类型 | 关联实体 | hidden |
|---|---|---|---|---|---|
| `system.currentLanguage` | 当前系统登录语言 | `currentLanguage` | STRING | - |  |
| `system.secretEnable` | 系统密级开关 | `secretEnable` | BOOLEAN | - |  |

## plugin（插件）— 1 项

| 全名 | 说明 | 短名 | 结果类型 | 关联实体 | hidden |
|---|---|---|---|---|---|
| `system.pluginList` | 插件列表 | `pluginList` | ARRAY | - |  |
