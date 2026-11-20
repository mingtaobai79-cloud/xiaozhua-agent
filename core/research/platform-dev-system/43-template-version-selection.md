# 43 · ★★★★★ 模板版本选择机制（完整闭环）

**证据来源**：`AbstractMultiVersionAutoCodeContext` / `TemplateAdapter` / `AutoCodeProperties` / `StringUtils.getMajorVersion` 反编译
**证据等级**：VERIFIED_STATIC_BYTECODE + LIVE（渲染实测吻合）

---

## 一、★★★★★ 完整链条

```
AutoCodeProperties.codeVersions = ["2.7", "2.8", "2.9", "3.0"]
                                    ↑ @ConfigurationProperties(prefix="seeyon.autocode")
   ↓
AbstractMultiVersionAutoCodeContext.getCodeVersion()
   = StringUtils.getMajorVersion(  udc-starter-autocode jar 的 version  )
   = getMajorVersion("5.3.605") = "5.3"        ← 期望版本
   ↓
wrapVersion(templatePath)
   = "/autocode/JAVA/" + "5.3" + templatePath
   ↓
TemplateAdapter.adaptTemplatePath(path, codeVersions, "5.3")
   ↓ LazyCacheUtils.getTemplatePath("/autocode/JAVA/5.3/xxx") → null（不存在！）
   ↓ 过滤 v < "5.3" → [2.7, 2.8, 2.9, 3.0] 全部满足
   ↓ 降序排序 → [3.0, 2.9, 2.8, 2.7]
   ↓ 逐个试 path.replace("5.3", version)
   3.0 → /autocode/JAVA/3.0/xxx   ← 存在则命中
   2.9 → /autocode/JAVA/2.9/xxx   ← 存在则命中
   ...
```

---

## 二、★★★★★ `getCodeVersion()` 的真实逻辑

```java
public String getCodeVersion() {
    String fullVersion = StringUtils.isNotBlank(this.codeVersion)
        ? this.codeVersion
        : Apps.depends().values().stream()
              .filter(b -> b.getArtifactId().equals("udc-starter-autocode"))
              .findFirst()
              .map(BuildInfo::getVersion)
              .orElseGet(() -> Apps.getBuildInfo().getVersion());
    return StringUtils.getMajorVersion(fullVersion);
}
```

### `getMajorVersion` 的真实实现

```java
public static String getMajorVersion(String version) {
    if (isEmpty(version)) return "";
    try {
        int pos = version.indexOf(".");
        pos = version.indexOf(".", pos + 1);      // ★ 找第二个点
        return version.substring(0, pos);          // ★ 截到第二个点前
    } catch (Exception e) {
        return version;
    }
}
```

**★★★★★ 结论：**
```
"5.3.605"  → 第一个点 idx=1，第二个点 idx=3  → substring(0,3) = "5.3"
"5.3"      → 第一个点 idx=1，第二个点 = -1   → substring(0,-1) 抛异常 → 返回 "5.3"
"5"        → 同上 → 返回 "5"
```

**⇒ 版本号的**主版本 = 前两段**（X.Y），不是 X。**
**⇒ `udc-starter-autocode` 5.3.605 → 期望模板目录 `5.3`。**

---

## 三、★★★★★ `wrapVersion` —— 路径改写规则

```java
public void wrapVersion(EarlyTemplate earlyTemplate) {
    String templatePath = earlyTemplate.getTemplatePath();
    if (!templatePath.contains("autocode")) {          // ★ 幂等保护
        String p = "/autocode/" + getCodeLanguage().name() + "/" + getCodeVersion() + templatePath;
        earlyTemplate.setTemplatePath(p);
    }
}

public String wrapVersion(String templatePath) {
    if (!templatePath.contains("autocode")) {
        return "/autocode/" + getCodeLanguage().name() + "/" + getCodeVersion() + templatePath;
    }
    return templatePath;
}
```

**★ `!contains("autocode")` 是幂等判断 —— 已包装过的路径不会被二次包装。**

**例：**
```
输入： "/entity/entity.java.ftl"
输出： "/autocode/JAVA/5.3/entity/entity.java.ftl"
```

---

## 四、★★★★★ `adaptTemplatePath` —— 三级回退

```java
public String adaptTemplatePath(String templatePath, List<String> codeVersions, String currentVersion) {
    // ① 缓存命中
    String existPath = compatibleMap.get(templatePath);
    if (existPath != null) return existPath;

    // ② 当前版本直接存在 → 不改写
    String currentPath = LazyCacheUtils.getTemplatePath(templatePath);
    if (currentPath == null) {
        // ③-a 先找「更低版本」，降序
        List<String> lowerVersionList = codeVersions.stream()
            .filter(v -> StringUtils.compareVersion(v, currentVersion) < 0)
            .collect(Collectors.toList());
        List<String> selectList = new ArrayList<>();
        if (CollectionUtils.isNotEmpty(lowerVersionList)) {
            lowerVersionList.sort((v1, v2) -> StringUtils.compareVersion(v2, v1));  // ★ 降序
            selectList = lowerVersionList;
        } else {
            // ③-b 没有更低版本 → 找「更高版本」，升序
            List<String> higherVersionList = codeVersions.stream()
                .filter(v -> StringUtils.compareVersion(v, currentVersion) > 0)
                .collect(Collectors.toList());
            if (CollectionUtils.isNotEmpty(higherVersionList)) {
                higherVersionList.sort(StringUtils::compareVersion);               // ★ 升序
                selectList = higherVersionList;
            }
        }
        // ④ 逐个替换版本号试探
        if (CollectionUtils.isNotEmpty(selectList)) {
            for (String version : selectList) {
                String selectVersion = templatePath.replace(currentVersion, version);
                if (LazyCacheUtils.getTemplatePath(selectVersion) == null) continue;
                log.info("代码生成模板自适应: {}->{}", templatePath, selectVersion);
                compatibleMap.put(templatePath, selectVersion);
                return selectVersion;
            }
        }
    }
    compatibleMap.put(templatePath, templatePath);
    return templatePath;
}
```

### ★★★★★ 四条规则

| # | 规则 |
|---|---|
| 1 | **优先降级**（找更低版本），降级时**从高到低**试 |
| 2 | 无更低版本才**升级**（找更高版本），升级时**从低到高**试 |
| 3 | 用 `templatePath.replace(currentVersion, version)` 做路径改写 |
| 4 | 结果进 `compatibleMap` 缓存，只算一次 |

---

## 五、★★★★★ `codeVersions` 的真实值

```java
@ConfigurationProperties(prefix = "seeyon.autocode")
public class AutoCodeProperties {
    private List<String> codeVersions = Arrays.asList("2.7", "2.8", "2.9", "3.0");
    ...
}
```

**⇒ 可以配置覆盖：`seeyon.autocode.code-versions=2.7,2.8,2.9,3.0`（Nacos 配置中心）。**

---

## 六、★★★★★ 实测吻合（LIVE 验证）

**实际渲染时的日志：**
```
代码生成模板自适应: /autocode/JAVA/5.3/entity/entity.java.ftl
                 -> /autocode/JAVA/3.0/entity/entity.java.ftl

代码生成模板自适应: /autocode/JAVA/5.3/service/xxxService.java.ftl
                 -> /autocode/JAVA/2.9/service/xxxService.java.ftl
```

**⇒ 完全解释了为什么 entity 类来自 3.0、其余来自 2.9。**

### 6.1 版本目录的模板分布

| 版本 | 模板数 | 有 entity.java.ftl | 有 baseservice.java.ftl |
|---|---|---|---|
| 2.7 | 125 | ✅ | ❌ |
| 2.8 | 138 | ✅ | ❌ |
| 2.9 | 141 | ❌ | ❌ |
| **3.0** | **2** | **✅** | **✅** |

**★★★★★ 这就是 2.9 → 3.0 的分层升级：**
```
3.0/entity/entity.java.ftl        13,272 字节
3.0/entity/baseservice.java.ftl   74,308 字节
```

**⇒ 平台把「实体类」和「BaseService」两个最核心的产物升级到 3.0，其余 141 个留在 2.9。**

**⇒ 这是**渐进式升级策略**：新版本只放改动过的模板，旧模板继续降级复用。**

---

## 七、★★★ 对开发者的实际影响

| 场景 | 影响 |
|---|---|
| 自定义模板放 `autocode/JAVA/2.9/` | 只在 2.9 命中，3.0 的 2 个模板不会用你的 |
| 改 `entity.java.ftl` | 必须放 `3.0/`，放 2.9 无效（2.9 没有该文件，且当前版本 5.3 优先找 3.0） |
| 想要所有模板都用 2.8 | 配 `seeyon.autocode.code-versions=2.8`，但 entity 会退到 2.8 |
| 模板路径已含 `autocode` | `wrapVersion` 跳过，直接按原路径用 |

---

## 八、★★★ 缓存行为

```java
private ConcurrentHashMap<String, String> compatibleMap = new ConcurrentHashMap();
```

**⇒ 每个 `TemplateAdapter` 实例一份缓存（单例 Bean），进程内有效。**
**⇒ 改了模板文件需要重启或清缓存才生效。**

---

## 九、待验证

| 问题 | 状态 |
|---|---|
| `Apps.depends()` 里 `udc-starter-autocode` 的 version 实际值 | UNVERIFIED（推断 5.3.605） |
| `LazyCacheUtils.getTemplatePath` 如何加载模板 | 待反编译 |
| `StringUtils.compareVersion` 的排序规则 | 待确认（看是否为数值比较） |
| 是否可以放 `5.3` 目录覆盖 | 理论上可以（当前版本直接命中） |