# devops-starter-artifact + devops-starter-common：制品上传下载与压缩归档

## Capability

**平台自己的「制品仓」与「压缩工具」两套**：

```
devops-starter-artifact   ArtifactManager / ArtifactService —— 构建产物上传下载、版本解析
devops-starter-common     压缩/解压处理器族（Zip/Jar/Tar/Gzip/7z）+ 通用工具
```

用途：客开在**部署/打包/插件分发**类需求里会碰；日常业务代码基本不用。

## Version

`devops-starter-artifact` 5.3.600 / `devops-starter-common` 5.3.600。

## ★ 一、ArtifactService（按仓库类型分工）

```java
public interface ArtifactService {
    MavenTypeEnum getMavenType();
    boolean upload(ArtifactDto) throws Exception;
    String  download(ArtifactDto);
    String  download(ArtifactDto, Supplier<Exception> onMissing);
    // default：offlineMode() / defaultMavenCmd() / getMvnBasePath() / buildLocalDownPath(String)
}
```

实现按 Maven 类型分（`ArtifactoryService` / `BucketMavenService` / `CmdService` …），
由上层的 `ArtifactManager` 选路。

## ★ 二、ArtifactManager（统一入口）

```java
static AbstractArtifactManager getArtifactManager(AppTypeEnum);   // 按应用类型选实现
boolean exist(ArtifactDto);
String  getLatestVersion(ArtifactDto);
List<String> resolveVersionRange(VersionRangeArtifactDto);        // ★ 解析版本区间
boolean upload(ArtifactDto);
boolean isFerryboatMavenMode();
ArtifactMavenProperties getMavenProperties();
String getMvnBasePath();
```

`ArtifactDto` 只有常量（`SNAPSHOT` 与 `SNAPSHOT_TIMESTAMP` 正则）挂在类上，字段全在父类 `BaseArtifactDto`。

## ★ 三、压缩/解压（devops-starter-common）

成对存在的处理器（字节码类名即契约）：

```
ZipArchiveHandler       / ZipUnArchiveHandler
JarArchiveHandler       / JarUnArchiveHandler
TarArchiveHandler       / TarUnArchiveHandler
GzipArchiveHandler      / GzipUnArchiveHandler
ServenZArchiveHandler   / ServenZUnArchiveHandler     ← 7z（平台自命名）
共同基类：AbstractArchiveHandler / AbstractUnArchiveHandler
```

判据：按后缀挑 handler，别自己写 `ZipInputStream`。

## Side Effects

- `upload` 会真的把制品推到仓库（Artifactory/桶/命令），**带版本号就是永久条目**（SNAPSHOT 除外）。
- `download` 落地路径由 `buildLocalDownPath` 决定，注意磁盘。
- 解压不校验路径穿越（zip-slip），解压外部上传的包时要自己校验条目路径。

## Known Constraints

1. `ArtifactManager` 是**静态选路**（`getArtifactManager(AppTypeEnum)`），不是注入一个 bean 了事。
2. 版本区间解析用 `resolveVersionRange`，别自己字符串比较（SNAPSHOT 时间戳格式特殊）。
3. `devops-starter-common` 只有压缩与通用工具，**没有业务能力**；别拿它当平台 SDK。
4. 这两个包属**发布链路**，客开业务代码里出现它们通常意味着设计跑偏了。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `ArtifactService` 6 方法 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `ArtifactManager` 9 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| 5 组压缩/解压处理器（含 7z 的 ServenZ） | 类清单 | VERIFIED_STATIC_BYTECODE |
| `ArtifactDto` 仅常量（SNAPSHOT 正则） | `javap -p` | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与方法可复核
- ⚠️ 未真机上传/下载（无制品仓凭据）

## 给 Agent 的判据

```
要取某应用最新制品版本   → ArtifactManager.getLatestVersion(ArtifactDto)
要判断制品是否存在       → exist(dto)
要解析 "[1.0,1.1)" 这类  → resolveVersionRange(VersionRangeArtifactDto)
要打包/解包             → Zip/Jar/Tar/Gzip/ServenZ 成对 handler
业务代码里想用这两个包    → 停一下，先确认不是把发布链路当成业务 SDK
```
