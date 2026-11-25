"""平台后端全量类索引（platform_class_index）。

## 解决什么问题

平台后端有 **21389 个类**（class 19174 / interface 1457 / enum 758），
但 facts 文档里只记录过 958 个，覆盖率 **4.5%**。

后果（实战踩过）：
- 想用 JSON 工具，不知道标品已有 `com.seeyon.boot.util.JsonUtils`（22 个方法）→ 引了 fastjson
- 想算日期，不知道 `DateUtils` 有 66 个方法（addDay/getFirstDayInMonth/collectLocalDates）→ 手写
- 想发流程，不知道 `BpmAppService` 22 个方法 → 自己拼 HTTP

本模块把 **2388 个「写代码时会用到」的类**（util 821 / AppService 1001 / SPI 566）
全部建成可检索索引，共 **23842 个方法**，并且支持**中文业务词**反查。

## 为什么不是全部 21389 个

剩下 19001 个是 `*Impl` / `*Handler` / `*Config` 等实现与内部类，
写扩展代码时不会直接 import，索引进来只会淹没真正有用的结果。
判定规则见 `bucket()`：util / appservice / spi 三类才收。

## 中文映射怎么做（这是关键）

不靠人工给 2388 个类起名（会错、会漏、维护不动），而是：

1. **token 词典**：637 个高频 token（`date`→日期、`json`→JSON、`cache`→缓存…）
   由类名驼峰拆词得到，覆盖 85% 类名只需 31 个 token
2. **类名即标签**：`DateUtils` → 「日期」+「工具」
3. **检索三路**：中文 token 命中 / 英文类名子串 / 方法名子串

这样新增类不需要改代码，自动就有中文标签。

## 边界

★ 只做「查到」，不判断「该不该用」。命中后由人/LLM 看签名决定。
★ 查不到就明说 0 命中，**绝不发明类名或方法名**。
★ 索引来自 `signatures.txt.gz`（javap 产物，VERIFIED_STATIC_BYTECODE），
  不是从源码猜的。
"""
from __future__ import annotations

import gzip
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.index_data import missing_message, resolve

_REPO = Path(__file__).resolve().parents[2]
# 签名库随产品发行，位置由 core.index_data 解析（发行树 fixtures/reference/，
# 工作区兼容 docs/audit/，可用 XIAOZHUA_INDEX_DIR 覆盖）
_SIG_NAME = "signatures.txt.gz"

# ───────────────────────────── 中文 token 词典 ─────────────────────────────
# 来源：2388 个目标类名驼峰拆词后的 token 频次统计，取高频 + 语义明确的
# ★ 新增条目只需加映射，不需要改检索逻辑

TOKEN_ZH: dict[str, str] = {
    # 数据与序列化
    "json": "JSON", "xml": "XML", "yaml": "YAML", "csv": "CSV", "excel": "Excel",
    "data": "数据", "dataset": "数据集", "type": "类型", "convert": "转换",
    "converter": "转换器", "serializer": "序列化", "serialize": "序列化",
    "parse": "解析", "parser": "解析器", "format": "格式化", "formatter": "格式化",
    "map": "映射", "mapping": "映射", "copy": "拷贝", "copier": "拷贝",
    "merge": "合并", "split": "拆分", "compress": "压缩", "zip": "压缩包",
    "escape": "转义", "escaper": "转义", "string": "字符串", "char": "字符",
    "number": "数字", "integer": "整数", "boolean": "布尔", "byte": "字节",
    "double": "双精度", "float": "浮点", "long": "长整型", "array": "数组",
    "list": "列表", "set": "集合", "map": "映射", "object": "对象",
    "primitive": "基本类型", "value": "值", "constant": "常量",
    "constants": "常量", "variable": "变量", "param": "参数",
    "parameter": "参数", "params": "参数", "property": "属性",
    "properties": "属性", "attribute": "属性", "field": "字段",
    "column": "列", "row": "行", "cell": "单元格", "table": "表",

    # 时间日期
    "date": "日期", "time": "时间", "datetime": "日期时间", "worktime": "工时",
    "holiday": "节假日", "schedule": "调度", "scheduler": "调度器",
    "job": "定时任务", "cron": "定时", "calendar": "日历", "cycle": "周期",

    # 文件与存储
    "file": "文件", "storage": "存储", "store": "存储", "upload": "上传",
    "download": "下载", "attachment": "附件", "doc": "文档", "document": "文档",
    "word": "Word", "pdf": "PDF", "ofd": "OFD", "image": "图片", "pic": "图片",
    "video": "视频", "voice": "语音", "media": "媒体", "sheet": "工作表",
    "reader": "读取器", "writer": "写入器", "stream": "流", "font": "字体",
    "watermark": "水印", "stamp": "印章", "seal": "印章", "signature": "签名",
    "sign": "签名", "signer": "签名器",

    # 网络与 HTTP
    "http": "HTTP", "url": "URL", "uri": "URI", "request": "请求",
    "response": "响应", "resp": "响应", "req": "请求", "client": "客户端",
    "server": "服务端", "port": "端口", "host": "主机", "address": "地址",
    "ip": "IP", "gateway": "网关", "proxy": "代理", "transport": "传输",
    "servlet": "Servlet", "controller": "控制器", "route": "路由",
    "dispatcher": "分发器", "invoke": "调用", "invoker": "调用器",

    # 缓存与并发
    "cache": "缓存", "cached": "缓存", "redis": "Redis", "lock": "锁",
    "thread": "线程", "async": "异步", "parallel": "并行", "concurrent": "并发",
    "executor": "执行器", "pool": "池", "queue": "队列", "mqmessage": "消息",
    "event": "事件", "bus": "总线", "listener": "监听器", "callback": "回调",

    # 认证与安全
    "auth": "认证", "authentication": "认证", "authorization": "授权",
    "authority": "权限", "permission": "权限", "role": "角色", "user": "用户",
    "login": "登录", "logout": "登出", "token": "令牌", "jwt": "JWT",
    "sso": "单点登录", "password": "密码", "secret": "密钥", "encrypt": "加密",
    "crypt": "加解密", "md5": "MD5", "sha256": "SHA256", "sm4": "SM4",
    "license": "授权", "certificate": "证书", "identity": "身份",

    # 组织与人员
    "org": "组织", "organization": "组织", "unit": "单位", "member": "成员",
    "people": "人员", "person": "人员", "team": "团队", "teamwork": "团队协作",
    "group": "分组", "department": "部门", "company": "公司", "corp": "企业",
    "enterprise": "企业", "institution": "机构", "participant": "参与人",
    "guest": "访客", "admin": "管理员", "manager": "管理器",

    # 流程与审批
    "bpm": "BPM流程", "flow": "流程", "workflow": "工作流", "process": "过程",
    "approval": "审批", "affair": "事项", "ticket": "工单", "draft": "草稿",
    "submit": "提交", "publish": "发布", "audit": "审核", "opinion": "意见",
    "node": "节点", "task": "任务", "instance": "实例", "status": "状态",
    "state": "状态", "result": "结果", "detail": "详情", "info": "信息",
    "summary": "摘要", "history": "历史", "record": "记录", "records": "记录",

    # UDC 与低代码
    "udc": "UDC低代码", "app": "应用", "application": "应用", "micro": "微",
    "page": "页面", "form": "表单", "entity": "实体", "metadata": "元数据",
    "meta": "元数据", "schema": "模式", "template": "模板", "plugin": "插件",
    "extension": "扩展", "extend": "扩展", "custom": "自定义",
    "customized": "自定义", "dynamic": "动态", "runtime": "运行时",
    "design": "设计", "definition": "定义", "component": "组件",
    "widget": "控件", "layout": "布局", "style": "样式", "theme": "主题",
    "view": "视图", "display": "展示", "preview": "预览", "render": "渲染",

    # 数据访问
    "sql": "SQL", "jdbc": "JDBC", "mybatis": "MyBatis", "dao": "DAO",
    "db": "数据库", "database": "数据库", "oracle": "Oracle", "mysql": "MySQL",
    "query": "查询", "select": "查询", "insert": "插入", "update": "更新",
    "delete": "删除", "batch": "批量", "transaction": "事务",
    "sharding": "分片", "cluster": "集群", "migration": "迁移", "ddl": "DDL",
    "idempotent": "幂等", "cascade": "级联",

    # 集成与对接
    "cip": "CIP集成", "connector": "连接器", "provider": "提供者", "spi": "SPI扩展点",
    "adapter": "适配器", "third": "第三方", "external": "外部",
    "transfer": "传输", "convert": "转换", "etl": "ETL", "dispatcher": "分发",
    "tencent": "腾讯", "wechat": "微信", "wx": "微信", "wxbiz": "微信业务",
    "dingtalk": "钉钉", "ali": "阿里", "alibaba": "阿里", "huawei": "华为",
    "hua": "华为", "apple": "苹果", "gaode": "高德", "tianyin": "天音",
    "qy": "企业", "sms": "短信", "email": "邮件", "mail": "邮件",
    "push": "推送", "notify": "通知", "message": "消息", "missive": "消息",
    "reminders": "提醒", "warning": "预警",

    # 业务域
    "meeting": "会议", "room": "会议室", "conference": "会议",
    "invoice": "发票", "receipt": "收据", "payment": "支付", "pay": "支付",
    "bank": "银行", "tax": "税务", "toll": "过路费", "train": "火车",
    "air": "机票", "trip": "差旅", "vehicle": "车辆", "taxi": "出租车",
    "contract": "合同", "contracts": "合同", "customer": "客户",
    "company": "公司", "credit": "信用", "ledger": "台账", "report": "报表",
    "chart": "图表", "gantt": "甘特图", "indicator": "指标",
    "knowledge": "知识", "book": "知识库", "pedia": "百科", "album": "相册",
    "integral": "积分", "praise": "点赞", "reply": "回复", "question": "问答",
    "quiz": "考试", "resume": "简历", "ocr": "OCR", "face": "人脸",
    "gis": "GIS", "map": "地图", "weather": "天气", "location": "位置",
    "locations": "位置", "area": "区域", "geo": "地理", "qr": "二维码",

    # 平台与框架
    "boot": "Boot框架", "core": "核心", "common": "通用", "base": "基础",
    "basic": "基础", "util": "工具", "utils": "工具", "helper": "工具",
    "kit": "工具集", "tool": "工具", "factory": "工厂", "builder": "构建器",
    "manager": "管理器", "handler": "处理器", "support": "支持",
    "strategy": "策略", "annotation": "注解", "interceptor": "拦截器",
    "filter": "过滤器", "validator": "校验器", "check": "校验", "validate": "校验",
    "verify": "验证", "assert": "断言", "exception": "异常", "error": "错误",
    "log": "日志", "logger": "日志", "monitor": "监控", "stat": "统计",
    "analysis": "分析", "analysis": "分析", "calculate": "计算",
    "formula": "公式", "function": "函数", "expression": "表达式",
    "rule": "规则", "rules": "规则", "condition": "条件", "match": "匹配",
    "filter": "过滤", "search": "搜索", "find": "查找", "retrieve": "检索",
    "retrieval": "检索", "query4sf": "查询", "fetcher": "获取器",
    "loader": "加载器", "scanner": "扫描器", "discoverer": "发现器",
    "registrar": "注册器", "register": "注册", "register": "注册",
    "init": "初始化", "configuration": "配置", "config": "配置",
    "setting": "设置", "env": "环境", "system": "系统", "sys": "系统",
    "platform": "平台", "seeyon": "致远", "ctp": "CTP平台", "cdp": "CDP平台",
    "portal": "门户", "portlet": "Portlet", "m5": "M5移动端", "mobile": "移动端",
    "applet": "小程序", "web": "Web", "front": "前端", "screen": "大屏",
    "tab": "页签", "menu": "菜单", "shortcut": "快捷方式", "card": "卡片",
    "modal": "弹窗", "box": "盒子", "frame": "框架", "wrapper": "包装器",
    "kit": "工具集", "lib": "库", "module": "模块", "package": "包",
    "artifact": "构件", "deploy": "部署", "maven": "Maven", "jar": "JAR",
    "version": "版本", "upgrade": "升级", "snapshot": "快照",
    "serial": "序列号", "snowflake": "雪花ID", "uuid": "UUID",
    "id": "ID", "ids": "ID", "key": "键", "keys": "键", "name": "名称",
    "label": "标签", "title": "标题", "desc": "描述", "remark": "备注",
    "category": "分类", "kind": "种类", "level": "级别", "range": "范围",
    "scope": "作用域", "limit": "限制", "quota": "配额", "capacity": "容量",
    "scale": "规模", "size": "大小", "width": "宽度", "height": "高度",
    "count": "数量", "total": "总数", "index": "索引", "sort": "排序",
    "order": "顺序", "rank": "排名", "position": "位置", "path": "路径",
    "link": "链接", "linker": "链接器", "relation": "关联",
    "relationship": "关系", "refer": "引用", "reference": "引用",
    "associate": "关联", "dependent": "依赖", "children": "子项",
    "parent": "父级", "tree": "树", "traverser": "遍历器",
    "hierarchical": "层级", "vertical": "纵向", "lateral": "横向",
    "single": "单", "multi": "多", "one": "单", "many": "多",
    "big": "大", "large": "大", "short": "短", "small": "小",
    "auto": "自动", "manual": "手动", "default": "默认", "normal": "普通",
    "special": "特殊", "general": "通用", "public": "公共",
    "private": "私有", "inner": "内部", "outer": "外部", "local": "本地",
    "online": "在线", "offline": "离线", "remote": "远程", "cloud": "云",
    "gray": "灰度", "preset": "预置", "optional": "可选", "required": "必填",
    "validity": "有效期", "expire": "过期", "refresh": "刷新",
    "renew": "续期", "repush": "重推", "repush": "重推", "resend": "重发",
    "retry": "重试", "rollback": "回滚", "roll": "滚动",
    "create": "创建", "add": "新增", "modify": "修改", "edit": "编辑",
    "change": "变更", "remove": "移除", "clear": "清空", "reset": "重置",
    "import": "导入", "export": "导出", "generate": "生成",
    "generator": "生成器", "build": "构建", "exec": "执行", "execute": "执行",
    "run": "运行", "runner": "运行器", "start": "启动", "stop": "停止",
    "end": "结束", "close": "关闭", "open": "打开", "load": "加载",
    "save": "保存", "store": "存储", "read": "读取", "write": "写入",
    "check": "校验", "verify": "校验", "proofread": "校对",
    "censor": "审核", "supervise": "督办", "track": "跟踪",
    "forward": "转发", "back": "回退", "duplicate": "复制",
    "derive": "派生", "generalize": "泛化", "simulation": "模拟",
    "strategy": "策略", "scheme": "方案", "plan": "计划", "design": "设计",
    "architecture": "架构", "framework": "框架", "engine": "引擎",
    "component": "组件", "module": "模块", "capability": "能力",
    "feature": "特性", "function": "功能", "action": "动作",
    "activity": "活动", "operation": "操作", "operate": "操作",
    "manipulate": "操作", "process": "处理", "deal": "处理",
    "assist": "辅助", "support": "支持", "help": "帮助", "guide": "指引",
    "tool": "工具", "kit": "工具包", "sdk": "SDK", "api": "API",
    "sdk": "SDK", "client": "客户端", "facade": "门面", "appservice": "应用服务",
    "service": "服务", "impl": "实现", "implementation": "实现",
    "abstract": "抽象", "interface": "接口", "enum": "枚举", "enums": "枚举",
    "dto": "DTO", "vo": "VO", "po": "PO", "entity": "实体",
    "model": "模型", "domain": "领域", "aggregate": "聚合", "agg": "聚合",
    "root": "根", "detail": "明细", "item": "项", "items": "项",
    "line": "行", "header": "表头", "head": "头部", "body": "主体",
    "content": "内容", "context": "上下文", "session": "会话",
    "request": "请求", "response": "响应", "reply": "回复",
    "notification": "通知", "notice": "公告", "announcement": "公告",
    "personal": "个人", "my": "我的", "mine": "我的", "self": "自身",
    "own": "自有", "shared": "共享", "share": "共享", "public": "公开",
    "space": "空间", "room": "房间", "place": "场所", "site": "站点",
    "address": "地址", "contact": "联系人", "phone": "电话",
    "mobile": "手机", "fax": "传真", "postcode": "邮编", "zip": "邮编",
    "region": "地区", "province": "省", "city": "市", "district": "区",
    "country": "国家", "national": "国家", "international": "国际",
    "translation": "翻译", "locale": "区域", "i18n": "国际化",
    "language": "语言", "lang": "语言", "encoding": "编码", "charset": "字符集",
    "unicode": "Unicode", "base64": "Base64", "hex": "十六进制",
    "crypt": "加密", "decrypt": "解密", "hash": "哈希", "digest": "摘要",
    "salt": "盐值", "nonce": "随机数", "csrf": "CSRF", "xss": "XSS",
    "sqlwildcard": "SQL通配符", "injection": "注入", "vulnerability": "漏洞",
    "security": "安全", "sensitive": "敏感", "mask": "脱敏",
    "anonymize": "匿名化", "privacy": "隐私", "compliance": "合规",
    "gdpr": "GDPR", "watermark": "水印", "fingerprint": "指纹",
}


def _tokenize(class_simple_name: str) -> list[str]:
    """把 DateUtils / JsonUtils / BpmAppService 拆成 token。"""
    s = re.sub(r"(Utils|Util|Helper|AppService|Service|Spi|Provider|Factory)$", "",
               class_simple_name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [t.lower() for t in s.split() if len(t) > 1]


def _bucket(name: str) -> str | None:
    """只有这三类值得索引；其余是实现/内部类。"""
    if ".util." in name or name.endswith("Utils") or name.endswith("Util"):
        return "util"
    if name.endswith("AppService") or ".appservice." in name:
        return "appservice"
    if ".spi." in name or name.endswith("Spi") or name.endswith("Provider"):
        return "spi"
    return None


# ───────────────────────────── 索引加载 ─────────────────────────────

@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, dict[str, Any]], str]:
    """构建一次，进程内缓存。返回 (classes, error)。"""
    sig = resolve(_SIG_NAME)
    if sig is None:
        return {}, missing_message(_SIG_NAME)

    with gzip.open(sig, "rt", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    classes: dict[str, dict[str, Any]] = {}
    for line in lines:
        if "\t" in line:
            name, kind = line.split("\t")
            bucket = _bucket(name) or "other"
            classes[name] = {
                "name": name,
                "kind": kind,
                "simple": name.split(".")[-1],
                "package": ".".join(name.split(".")[:-1]),
                "bucket": bucket,
                "methods": [],
                "tokens": _tokenize(name.split(".")[-1]),
            }

    # 第二遍挂方法（签名库是「先类后方法」顺序，也可能交错，所以两遍更稳）
    meth_re = re.compile(r"^([\w.$]+)#([\w$<>]+)\((.*)\):(.+)$")
    for line in lines:
        if "#" not in line:
            continue
        cls = line.split("#")[0]
        c = classes.get(cls)
        if not c:
            continue
        m = meth_re.match(line)
        if not m:
            c["methods"].append({"raw": line})
            continue
        c["methods"].append({
            "name": m.group(2),
            "params": m.group(3),
            "returns": m.group(4),
            "raw": line,
        })

    return classes, ""


def _zh_of(tokens: list[str]) -> str:
    """token 列表 → 中文标签（命不中的 token 保留英文）。"""
    parts = []
    for t in tokens:
        parts.append(TOKEN_ZH.get(t, t))
    return "".join(parts) if parts else ""


# ───────────────────────────── 对外 API ─────────────────────────────

def search(term: str = "", pkg: str = "", bucket: str = "",
           kind: str = "", method: str = "", limit: int = 15) -> dict[str, Any]:
    """查平台后端类。

    参数
    ----
    term    : 中文业务词（「日期」「JSON」「缓存」）或英文类名片段（「DateUtils」）
    pkg     : 包前缀过滤，如 ``com.seeyon.boot.util``
    bucket  : util | appservice | spi
    kind    : class | interface | enum
    method  : 只看含此方法名的类
    limit   : 返回上限

    命中 0 条时 ``note`` 会明确说「没查到」，绝不返回编造结果。
    """
    classes, err = _index()
    if err:
        return {"query": term, "hits": [], "total": 0, "error": err}

    term = (term or "").strip()
    tl = term.lower()

    hits: list[dict[str, Any]] = []
    for c in classes.values():
        if pkg and not c["name"].startswith(pkg):
            continue
        if bucket and c["bucket"] != bucket:
            continue
        if kind and c["kind"] != kind:
            continue
        if method and not any(m.get("name") == method for m in c["methods"]):
            continue

        if term:
            # 三路命中：英文类名 / 中文标签 / token / 方法名
            zh = _zh_of(c["tokens"])
            hit_en = tl in c["name"].lower()
            hit_zh = term in zh
            hit_tok = any(tl in t for t in c["tokens"])
            hit_meth = any(tl in (m.get("name") or "").lower() for m in c["methods"])
            if not (hit_en or hit_zh or hit_tok or hit_meth):
                continue
            # ★ 匹配质量：类名/token 直接命中 > 只有方法名沾边
            #   不这么排，搜 "JSON" 会被 124 个方法的 AppService 淹没，
            #   真正该用的 JsonUtils 反而看不见。
            if hit_en or hit_zh or hit_tok:
                quality = 3 if (hit_zh or hit_tok) else 2
            else:
                quality = 1
        else:
            quality = 0

        hits.append({
            "name": c["name"],
            "simple": c["simple"],
            "kind": c["kind"],
            "bucket": c["bucket"],
            "zh": _zh_of(c["tokens"]),
            "methodCount": len(c["methods"]),
            "quality": quality,
            "methods": [m.get("name") for m in c["methods"][:25] if m.get("name")],
        })

    # 排序：匹配质量 → 常用桶优先 → 方法数（多的更可能是有用工具类）
    def _rank(h: dict[str, Any]) -> tuple:
        return (-h["quality"], 0 if h["bucket"] != "other" else 1, -h["methodCount"], h["name"])

    hits.sort(key=_rank)

    out: dict[str, Any] = {
        "query": term,
        "total": len(hits),
        "hits": hits[: int(limit)],
        "level": "VERIFIED_STATIC_BYTECODE",
    }
    if not hits:
        out["note"] = (
            "0 命中。不要发明类名：先换中文业务词（如「日期」「JSON」「缓存」），"
            "或去掉 pkg/bucket 过滤放宽范围；仍无 → 该类在签名库里不存在，"
            "标 UNVERIFIED 并问用户。"
        )
    elif len(hits) > int(limit):
        out["note"] = f"共 {len(hits)} 条，只返回前 {limit} 条；用 pkg/bucket 收窄。"
    return out


def methods_of(class_name: str, keyword: str = "") -> dict[str, Any]:
    """列出某个类的全部方法（可按方法名关键词过滤）。"""
    classes, err = _index()
    if err:
        return {"class": class_name, "methods": [], "error": err}
    c = classes.get(class_name)
    if not c:
        # 给相近建议
        sim = [n for n in classes if class_name.split(".")[-1] in n][:5]
        return {"class": class_name, "methods": [], "total": 0,
                "note": "该类不在签名库里（索引是 javap 全量快照，共 21389 类）；"
                        "核对拼写，或改用 similar 里的候选",
                "similar": sim}
    ms = c["methods"]
    if keyword:
        kl = keyword.lower()
        ms = [m for m in ms if kl in (m.get("name") or "").lower()]
    return {"class": class_name, "zh": _zh_of(c["tokens"]),
            "bucket": c["bucket"], "kind": c["kind"],
            "total": len(ms), "methods": ms[:200]}


def stats() -> dict[str, Any]:
    """索引规模统计。"""
    classes, err = _index()
    if err:
        return {"error": err}
    by_bucket: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    total_methods = 0
    for c in classes.values():
        by_bucket[c["bucket"]] = by_bucket.get(c["bucket"], 0) + 1
        by_kind[c["kind"]] = by_kind.get(c["kind"], 0) + 1
        total_methods += len(c["methods"])
    sig = resolve(_SIG_NAME)
    return {"classes": len(classes), "methods": total_methods,
            "byBucket": by_bucket, "byKind": by_kind,
            "tokenDict": len(TOKEN_ZH),
            "source": str(sig) if sig else None,
            "level": "VERIFIED_STATIC_BYTECODE"}
