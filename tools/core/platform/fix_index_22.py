#!/usr/bin/env python3
"""INDEX.md 加第 22 格（AppService 调用通路）。"""
from pathlib import Path

P = Path("<XIAOZHUA_AGENT_ROOT>/core/facts/INDEX.md")
NEW = (
    "㉒`appservice-invocation.md` **AppService 调用通路**（怎么把方法真正调起来：两条通路——"
    "① Spring 注入 `@Autowired BpmAppService` + `SingleRequest.from(dto)` + "
    "`response.getData().getContent()`；② 泛化调用 `AppServiceProxy.invokeAppService` + "
    "`AppServiceInvokeDto` 10 字段（interfaceName/methodName/paramType/genericType/subGenericType/"
    "paramJson/beanName/returnJson/bodyZip）；**关键**：泛化不是 Dubbo 是本地 Spring BeanFactory "
    "反射，6 层 Bean 查找兜底（末段首字母小写 → 接口全名 → ModuleAppBeanCache → 动态 Bean 名 → "
    "beanName → getBeansOfType 跳过 mock），全找不到抛 BOOT_4014；`@AppService`=@Service+@Primary "
    "才是可调前提，普通 `domain/service/XxxService` 不能泛化调；命名不规则——"
    "`BpmAppService` 的实现是 `BpmApiAppServiceImpl`，必须读 impl-map.json 不能猜）。"
)


def main() -> int:
    t = P.read_text(encoding="utf-8")
    t = t.replace("| standard-product | 21 格平台能力（包用法，环境无关） |",
                  "| standard-product | 22 格平台能力（包用法，环境无关） |")
    if "㉒" in t:
        print("已存在 ㉒")
        return 0
    anchor = "证据 `docs/audit/artifacts/extension-surface-20261029"
    i = t.find(anchor)
    if i == -1:
        print("ERR: 找不到锚点")
        return 5
    t = t[:i] + NEW + t[i:]
    P.write_text(t, encoding="utf-8")
    print("已插入 ㉒")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
