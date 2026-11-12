# 客户模块实现面对照核验（spi-mobile / spi-sso）

采集时刻: 2026-10-08T04:29Z（date -u 实测）　分级: 平台侧=VERIFIED_STATIC_BYTECODE；模块侧=源级在盘 + 模块字节码未取证

## A. 模块源侧（只读实测，0 网络）
| 命令 | RC | 实测结果 |
|---|---|---|
| `find custom-backend/spi-{mobile,spi-sso} -type f` | 0 | 各 5 件: `pom.xml`、`src/main/java/com/seeyon/extend/spi/sso/TemplateSsoServiceImpl.java`、`src/main/resources/META-INF/spring.factories`、`src/main/resources/metadata/spi_info.json`、`third-jar/README.md` |
| `cat …/META-INF/spring.factories` | 0 | 单键单值: `com.seeyon.cip.connector.api.sso.SsoService=\` → `com.seeyon.extend.spi.sso.TemplateSsoServiceImpl`（两模块字节相同） |
| `grep -c "implements" …/TemplateSsoServiceImpl.java` | 0 | 1 → `public class TemplateSsoServiceImpl implements SsoService`（两模块一致） |
| `grep -rhoE "com\.seeyon\.cip\.connector\.api\.[A-Za-z.]+" …/src \| sort -u` | 0 | 仅出现 `com.seeyon.cip.connector.api.sso.SsoService` 一项；`…api.mobile.*`、`…api.midorgsync.*`、`…api.callback.*`、`…api.sign.*`、`…api.affair.*`、`…api.authentication.*`、`…api.db.*` 0 命中 |
| `grep -c "@Override" …/TemplateSsoServiceImpl.java` | 0 | 7（与 `sso.SsoService.javap-p.txt` 的 7 个 abstract 方法数一致） |
| `find … \( -name "*.class" -o -name "*.jar" \) \| wc -l` | 0 | mobile=0、sso=0（模块无本地编译产物） |

## B. 平台侧字节码对应（见本目录 javap 件）
- `api-interfaces-list.txt`（RC=0）: `com/seeyon/cip/connector/api/**` 共 **20** 个条目，全部为 `public interface`（`mobile-group` 8 + `nonmobile-group` 12 = 20，`grep -c "public interface"` 实测）。
- `sso.SsoService.javap-p.txt`（RC=0）: 7 个 abstract 方法，模块侧 7 个 `@Override` 与之对应。
- `mobile-group.javap-p.txt`（RC=0）: 8 个 mobile 接口，`MobileProviderService` 为根，其余 7 个 `extends MobileProviderService`（`MobileCallBackProviderService` 另 `extends ConnectorCallbackProviderService<T,Res>`）。

## C. 结论与限制
1. 两模块对 `cip-connector-api` 扩展点全集的实际实现边界 = **注册并实现 1 个（`api.sso.SsoService`）／未实现其余 19 个**（含 mobile 组 8 个）。负结果由源侧（implements 子句 + spring.factories 键 + api 包 import 0 命中）三方一致支撑。
2. 模块侧字节码 = **未取证 UNVERIFIED**：模块无 `.class`/`.jar` 在盘（A 表末行实测 0），故模块的 implements 关系只有源级证据，无模块字节码复核。
3. 运行态是否加载/调用上述任一接口 = **未测试**（本批 0 网络）。
4. `spi_info.json` 两模块同为 `{"name":"boot-starter-spi-customized","scopes":["<租户标识串>"]}`；登记插件包名，不构成接口级实现证据。
