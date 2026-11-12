# 客开代码仓库：地址是环境配置，路径规则才是事实

> 证据级：**LIVE READONLY**（nacos 配置原文 `repo.gitlab`）+ **VERIFIED_STATIC**（本机 clone 的 remote 实测）
> 本格只回答「仓库里哪些能当规则用、哪些必须由调用方给」。

## 一、能确定的：路径规则

同一个环境里，后端与前端是两个独立仓库，**同构**：

```
<git-base>/backend/<appName>.git
<git-base>/frontend/<appName>.git
```

- `<appName>` = 平台给的应用目录名，通常 `<应用标识><appId>`
- `<git-base>` **是环境配置，不是常量**

## 二、不能当规则用的：域名与仓库组

❌ **禁止硬编码**具体域名或仓库组名。

理由：
- 域名（`<host>`）随客户变，每个客户一套
- 仓库组（`<repo-group>`，实测形态 `extend-<env>`）随环境变，每个环境一组
- 换一个环境，硬编码的地址直接 404，而且报错是「仓库不存在」，
  会把人带到「应用没建仓库」的错误方向上

`<git-base>` 的正确来源，按优先级：

**① nacos 配置（权威，已取证）**

平台把代码仓配置放在应用级 dataId（group = `seeyon`）里，键路径固定：

```yaml
repo:
  type: gitlab
  localBaseDir: /code/udc-code        # 平台容器内的代码工作目录
  gitlab:
    apiUrl: <gitlab 地址>              # 例：https://<host>
    parentGroupPath: <标品组>          # 例：autocode-<env>
    parentExtendGroupPath: <客开组>    # 例：extend-<env>
    privateTokenValue: <REDACTED>
```

于是：

```
<git-base> = {apiUrl}/{parentExtendGroupPath}      # 客开工程
<git-base> = {apiUrl}/{parentGroupPath}            # 标品工程（少数场景）
```

实测两套环境的差异（同一域名，组名随环境走）：

| 环境 | apiUrl | parentExtendGroupPath | parentGroupPath |
|---|---|---|---|
| uat | `https://<host>` | `extend-uat` | `autocode-uat` |
| test2 | `https://<host>` | `extend-test2` | `autocode-test2` |

★ 所以「域名可换」的正确含义是：**域名和组名都在 nacos 里，读配置即可，不要写死任何一段。**
★ 取证方式（只读）：`GET /v1/cs/configs?dataId=<dataId>&group=seeyon&tenant=<namespace>`，取 `repo.gitlab` 段。

**② 调用方显式传**

**③ 已有 clone 的 `remote.origin.url` 反推**（本机有仓库时最快）

**④ 都没有 → 报「需要 git-base」，不要猜**

## 三、平台有没有 git 地址接口 —— 没有接口，但 nacos 里有配置

**结论先说**：UDC 设计面没有「返回 git 地址」的接口；地址本身写在 nacos 应用级配置的
`repo.gitlab` 块里（见 §二 ①）。换句话说，**地址不是平台算出来的，是运维配的**。

查证过程（都是 0 命中，留档避免重复找）：

| 查过的地方 | 结果 |
|---|---|
| `udcApplicationGet` | 返回体无 git 字段 |
| `docs/operation-contracts/udc/application/udc-app-deploy-info-live-contract.md` | 无 git 相关字段 |
| 全局 grep `gitUrl` / `repoUrl` / `repositoryUrl` / `gitAddress` | 0 命中 |
| `core/facts/deploy/build-chain.md:56` | 原文写 UNVERIFIED（该处应改为指向本格） |

抓到配置的路径：`docs/audit/artifacts/u6-nacos-config/raw-02-nacos-configs.md`
（LIVE READONLY，全部 GET；见该文件头部只读纪律声明）。

**`localBaseDir: /code/udc-code` 的含义**：平台容器里有一份被管理的代码工作目录。
如果要在平台侧看真实工程结构，进 pod 看这个目录比猜快，但**不要在里面改**（会被平台覆盖）。

## 四、两个真实的工程形态（别假设只有一种）

### 形态 A：平台生成的五模块工程

```
backend/
├── pom.xml            <modules> 列下面五个
├── <appName>-facade/
├── <appName>-biz/
├── <appName>-web/
├── <appName>-ext/     ← 唯一可写
└── <appName>-assemble/
```

根包 `com.seeyon.<appName>`。**只有 `-ext/extend/` 能写**，其余四个重新构建即整包覆盖。

来源：`core/facts/standard-product/extension-project-skeleton.md`

### 形态 B：单模块工程（= 客开工程，标准形态）

```
backend/
├── pom.xml            （无 <modules>）
└── src/main/java/com/seeyon/<appName>/
    └── extend/        ← 客开代码
        ├── annotation/
        ├── context/
        ├── domain/
        ├── dto/
        ├── enums/
        ├── utils/
        └── web/
```

实测样本：本机已 clone 的一个 UDC 应用后端仓库就是这个形态，`pom.xml` 没有 `<modules>`。

**同一套规则下两种形态并存** → 生成代码前必须先探形态，不能默认五模块。
形态与来源模板的对应关系见 `autocode-project-templates.md` §2。

## 五、代码该写在哪（按目标分）

| 目标 | 五模块形态 | 单模块形态 |
|---|---|---|
| 自定义服务接口 | `<appName>-facade/.../custom/service/` | `src/main/java/com/seeyon/<appName>/extend/` 下自定包 |
| 自定义服务实现 | `<appName>-biz/.../custom/appservice/` | 同上 |
| SPI / 扩展点实现 | `<appName>-ext/.../extend/` | `extend/` |
| 前端自定义页面 | `pc/src/pages/<pageUrl>/customPage.tsx` | 同左（前后端仓库分离，格式一致） |

★ 单模块形态下「自定义服务」放哪个包 —— **已取证，见下**。

**单模块 = 客开工程的标准形态，不是异常。** 平台 autocode 有两套模板：

```
templates/project/backend/      标品工程  → -assemble / -biz / -facade / -web + 根 POM
templates/project-ext/backend/  客开工程  → 只有 -ext 一个模块
```

所以样本仓只有 `extend/` 是对的（`project-ext` 模板里也只生成
`${appPath}/extend/package-info.java` 一个文件）。

**自定义服务的代码不是手写的，是平台按 `templates/microflow/customflow/` 生成的**：

```
facade 接口        ${appServicePackage}
AppService 实现    ${appPackagePath}.custom.appservice.microflow
service 接口       ${appPackagePath}.custom.service.microflow
```

生成的方法体是 `throwUnimplemented()` 空壳，人只填实现。
链路：设计器建类型+出入参 → 平台生成骨架 → 推拉代码 → 填方法体 → 构建 → 微流程搜得到。

详见 `autocode-project-templates.md`（含 7 个模板文件名与证据路径）。

## 六、前端侧确定的部分

```
路径    pc/src/pages/<pageUrl>/customPage.tsx
产物    custom-page-<pageUrl>.js
路由    /main/portal/<appName>/<pageUrl>
```

★ 新建目录后必须重启 dev server —— `syf dev-udc-custom` 启动时一次性
`glob.sync('src/pages/**/customPage.tsx')`，之后建的目录永远不识别
（表现是页面显示 `hello world`）。见 `core/facts/udc/page/custom-page-dev-server-glob.md`。

## 七、别踩的坑

- **不要在工具里写死域名**。传参，或从已有 clone 反推。
- **不要假设五模块**。先看 `pom.xml` 有没有 `<modules>`。
- **不要往 facade/biz/web/assemble 写**。下次构建全丢，无提示无告警。
- **不要假设 `extend/` 有预置扩展点**。平台生成的 ext 默认只有 `extend/package-info.java`，
  一个钩子都不预置，所有扩展行为都要自己写、自己注册（没有 META-INF/services，
  也没有 spring.factories 自动装配）。
