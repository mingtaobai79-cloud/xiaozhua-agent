"""P5.3 平台验证与构建验证。

★ 严格复用已有事实，不新造接口：
  - 构建触发：POST /service/udc/runtime/deploy-normal
              body 必须包成 {"deployDto": {...}}（@MultiRequestBody）
              ★ 平铺即 DTO=null → EL1007E（已 LIVE 确诊）
  - 构建进度：GET /udc/sandbox/delta-build-info/{appId}
              返回 {state: BUILDING|SUCCESS|FAILED, progress, totalTime, logs[]}
  - 构建日志：backBuild.log（构建产物里）

★ 两条不可违背的语义（任务书）：
  1. 构建成功 ≠ 微流程真实运行成功。本模块只报构建事实，不吹运行。
  2. 一致性检测未过则整单 state=2，**没有部分成功**。必须原样反映。
"""

from __future__ import annotations

import dataclasses as dc
import json
import time


class BuildError(RuntimeError):
    pass


@dc.dataclass
class BuildResult:
    ok: bool
    state: str = ""              # BUILDING / SUCCESS / FAILED / TIMEOUT
    progress: str = ""
    total_time: str = ""
    deploy_id: str = ""
    log_tail: list[str] = dc.field(default_factory=list)
    problems: list[str] = dc.field(default_factory=list)
    detail: dict = dc.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "state": self.state, "progress": self.progress,
                "total_time": self.total_time, "deploy_id": self.deploy_id,
                "log_tail": self.log_tail, "problems": self.problems,
                "detail": self.detail}


#: 终态判定。★ BUILDING 不是终态，不能当成功。
TERMINAL_STATES = {"SUCCESS", "FAILED", "FAIL", "ERROR"}

#: 平台成功码。★ 是字符串 "BOOT_0000"，不是数字 0。
SUCCESS_CODES = {0, "0", "BOOT_0000", None}


def _is_success_code(code) -> bool:
    """平台成功码判定（BOOT_0000 / 0 / None 都算成功）。"""
    return code in SUCCESS_CODES


class PlatformBuilder:
    """构建触发 + 状态轮询 + 失败证据留存。

    参数：
        http      : 需要实现 post_json(path, body) / get_json(path) 的客户端
                    （默认用 CurlBackend 同族的 HTTP 封装；测试注入假对象）
        app_id    : 应用 ID
        poll_interval / timeout_s : 轮询节奏（★ 有上界，不无限等）
        sleep     : 可注入的 sleep（测试用）
    """

    DEPLOY_PATH = "/service/udc/runtime/deploy-normal"
    BUILD_INFO_PATH = "/service/udc/sandbox/delta-build-info/%s"

    # ★★ 按 deployId 查构建状态（唯一正确入口，2026-11-01 实测）
    #
    # delta-build-info 对 RELEASE 构建**根本不写**：它只留最近一次完成的
    # delta 结果。拿它轮询 RELEASE 构建会一直读到上一次的旧记录，
    # 加 _is_stale 后就是「永远 stale → 一直等到超时」。
    # 实测：RELEASE 触发后连查 10 分钟 delta-build-info 仍是 10-31 的 FAIL，
    # 而 search-deploy-status 一查就是 state=SUCCESS。
    #
    # GraphQL 三个坑（都实测过）：
    #   类型名必须是 ...PostInputPath（...PostInputBody / ...PostInput / ...Path 全部 UnknownType）
    #   参数必须是 path: {deployId}（path: "<str>" 报 java.lang.String cannot be cast to java.util.Map）
    #   返回 {data:{data0:{code,data:{content:[{...}]}}}}
    DEPLOY_STATUS_OP = "udcRuntimeSearchDeployStatusDeployIdPost"
    DEPLOY_STATUS_PATH = "/service/udc/graphql?udcRuntimeSearchDeployStatusDeployIdPost"
    DEPLOY_STATUS_Q = (
        "query g($p: udcRuntimeSearchDeployStatusDeployIdPostInputPath) {"
        " data0: udcRuntimeSearchDeployStatusDeployIdPost(path: $p)"
        " { code data { content } message } }")

    def deploy_status(self, deploy_id: str) -> dict:
        """按 deployId 读构建状态。读不到返回 {}（调用方必须判空）。"""
        body = {"query": self.DEPLOY_STATUS_Q,
                "variables": {"p": {"deployId": str(deploy_id)}}}
        try:
            r = self.http.post_json(self.DEPLOY_STATUS_PATH, body) or {}
        except Exception:
            return {}
        data = ((r.get("data") or {}).get("data0")
                or (r.get("data") or {}).get("data0") or {})
        if not isinstance(data, dict):
            return {}
        # 真实结构：{data:{data0:{code, data:{content:[{...}]}}}}
        # content 在 data0.data 里，不在 data0 顶层。
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        content = inner.get("content") or data.get("content") or []
        if isinstance(content, dict):
            content = [content]
        if not content:
            return {}
        return dict(content[0] or {})

    def __init__(self, *, http, app_id: str, poll_interval: float = 10.0,
                 timeout_s: float = 900.0, sleep=time.sleep):
        self.http = http
        self.app_id = app_id
        self.poll_interval = poll_interval
        self.timeout_s = timeout_s
        self.sleep = sleep

    # ---------------- 触发 ----------------
    def trigger(self, *, deploy_type: str = "RELEASE",
                project_type: str = "ALL", terminal_type: str = "ALL") -> str:
        """触发构建，返回 deployId。

        ★ body 必须包在 deployDto 里（@MultiRequestBody，平铺即 EL1007E）。

        ★★ deploy_type 默认 RELEASE，不是 TEST：
          设计器「测试」→「立即构建」发的就是 deployType=RELEASE
          （DeployTypeEnum.RELEASE 在 UDC 里表示「测试发布」，
           ON_ONLINE 才是上架，被「先测试后上线」闸门挡着）。
           实测用 TEST 触发时 delta-build-info 一直返回上一次的旧记录
           （2026-11-01：连查 8 分钟仍是 10-31 的 FAIL），新构建根本没起；
           换 RELEASE 后旧记录立刻被清空 → 构建真的开始了。
        """
        body = {"deployDto": {
            "appId": self.app_id,
            "deployType": deploy_type,
            "projectType": project_type,
            "terminalType": terminal_type,
        }}
        r = self.http.post_json(self.DEPLOY_PATH, body) or {}
        # ★ 平台成功码是字符串 "BOOT_0000"（也见过 0 / "0"），
        #   只认数字 0 会把每次成功都判成失败。
        if not _is_success_code(r.get("code")):
            # 平台错误码原样上报，不吞
            raise BuildError("构建触发失败 code=%s msg=%s"
                             % (r.get("code"), r.get("message")))
        # ★ 响应两层包裹：{data:{content:{deployId,...}}}。
        #   直接读 data.deployId 会拿到 None，误判成「没触发」。
        data = r.get("data") or {}
        if isinstance(data, dict) and isinstance(data.get("content"), dict):
            data = data["content"]
        deploy_id = str(data.get("deployId") or data.get("id") or "")
        if not deploy_id:
            raise BuildError("构建触发未返回 deployId：%r" % (r,))
        return deploy_id

    # ---------------- 轮询 ----------------
    def snapshot(self) -> dict:
        """读一次构建信息（已拆两层包裹），供 wait 判新旧用。"""
        try:
            st = self.http.get_json(self.BUILD_INFO_PATH % self.app_id) or {}
        except Exception:
            return {}
        data = st.get("data") if isinstance(st.get("data"), dict) else st
        if isinstance(data, dict) and isinstance(data.get("content"), dict):
            data = data["content"]
        return dict(data or {})

    @staticmethod
    def _is_stale(snap: dict, baseline: dict | None) -> bool:
        """这个快照是不是「上一次构建」的残留结果。

        ★ delta-build-info 只保留**最近一次完成**的结果：
          - 新构建进行中 → 返回全空（state=None）
          - 新构建还没覆盖 → 返回上一次的终态（可能是 FAIL）
        不判新旧的话，wait 会立刻读到上一次的 FAIL 并误判本次失败，
        或者读到上一次的 SUCCESS 误判本次成功。
        """
        if not baseline or not snap.get("state"):
            return False                      # 无基线/无结果，不按陈旧处理
        ss, bs = snap.get("startTime"), baseline.get("startTime")
        if ss and bs:
            return ss <= bs                   # 同一或更早 → 旧构建
        sv, bv = snap.get("buildVersion"), baseline.get("buildVersion")
        if sv and bv and sv != bv:
            return False                      # 版本变了 → 新构建
        if not ss and not bs:
            # 两边都没时间戳：状态和基线一致就认为是旧的
            return str(snap.get("state") or "").upper() == \
                   str(baseline.get("state") or "").upper()
        return False

    def wait(self, deploy_id: str = "", baseline: dict | None = None) -> BuildResult:
        """轮询到**本次**构建的终态或超时。★ BUILDING 不算成功。

        ★ 有 deploy_id 时走 search-deploy-status（按 id 精确查）；
          没有才退回 delta-build-info（只对 delta 构建有效）。
          实测：RELEASE 构建从不写 delta-build-info，拿它轮询必然超时。
        """
        started = time.time()
        last: dict = {}
        stale_seen = 0
        empty_seen = 0
        use_id = bool(str(deploy_id or "").strip())
        while time.time() - started < self.timeout_s:
            try:
                data = {}
                from_status = False
                if use_id:
                    data = self.deploy_status(deploy_id)
                    from_status = bool(data)
                if not data:
                    # ★ 回退：delta-build-info（只对 delta 构建有效）。
                    #   真实 RELEASE 场景 status 一定读得到，回退只发生在
                    #   接口/登录态异常时，让调用方拿到旧记录后由 _is_stale 判。
                    st = self.http.get_json(self.BUILD_INFO_PATH % self.app_id) or {}
                    # ★ 平台响应有两层包裹：{status, code, message, data:{content:{...}}}
                    data = st.get("data") if isinstance(st.get("data"), dict) else st
                    if isinstance(data, dict) and isinstance(data.get("content"), dict):
                        data = data["content"]
            except Exception as e:
                # 单次读取失败不立刻判死，但要有上界
                last = {"error": str(e)}
                self.sleep(self.poll_interval)
                continue
            last = data or {}
            if not last:
                # ★ 读不到不算「还在构建」。连续读不到要有上界，
                #   否则 sleep 很快的实现会空转到超时，看起来像「一直在构建」。
                empty_seen += 1
                if empty_seen >= 20:
                    return BuildResult(
                        ok=False, state="UNREADABLE", deploy_id=deploy_id,
                        problems=["连续 %d 次读不到构建状态（接口/登录态/参数问题，"
                                  "不是构建慢）" % empty_seen],
                        detail={"last": last, "empty_seen": empty_seen})
                self.sleep(self.poll_interval)
                continue
            empty_seen = 0
            state = str(last.get("state") or "").upper()
            if state in TERMINAL_STATES:
                # ★ 按 deployId 查到的结果本来就属于本次构建，不需要判新旧；
                #   只有回退到 delta-build-info 时才可能是上一次的残留。
                if not from_status and self._is_stale(last, baseline):
                    stale_seen += 1           # 旧结果，继续等新构建
                    self.sleep(self.poll_interval)
                    continue
                return self._verdict(state, last, deploy_id)
            self.sleep(self.poll_interval)
        # 超时：不算成功
        problems = ["构建轮询超时（%.0fs 内未到终态）" % self.timeout_s]
        if stale_seen:
            problems.append("期间读到 %d 次上一次构建的残留结果（已忽略）" % stale_seen)
        return BuildResult(ok=False, state="TIMEOUT",
                           progress=str((last or {}).get("progress") or ""),
                           deploy_id=deploy_id,
                           problems=problems,
                           detail={"last": last, "stale_seen": stale_seen})

    def _verdict(self, state: str, last: dict, deploy_id: str) -> BuildResult:
        logs = last.get("logs") or []
        tail = [str(x) for x in logs[-20:]]
        ok = state == "SUCCESS"
        problems: list[str] = []
        if not ok:
            # ★ 失败必须保留完整错误证据（含一致性检测未过的情形）
            problems = [ln for ln in tail if "ERROR" in ln or "失败" in ln][:10] or tail[:10]
        return BuildResult(
            ok=ok, state=state,
            progress=str(last.get("progress") or ""),
            total_time=str(last.get("totalTime") or ""),
            deploy_id=deploy_id, log_tail=tail, problems=problems,
            detail={"validate": last.get("validate"),
                    "buildVersion": last.get("buildVersion")},
        )

    # ---------------- 一步到位 ----------------
    def build(self, **kw) -> BuildResult:
        """触发 + 轮询。编排器 P5.1 调的就是这个方法。

        ★ 触发前先拍基线快照：delta-build-info 只留最近一次完成结果，
          不拍基线就无法区分「本次构建」和「上一次残留」。
        ★★ UDC_DEPLOY_0002（app publishing）= 应用正在发布（构建锁），
          是暂时状态，重试等待而不是直接失败。
        """
        baseline = self.snapshot()
        deploy_id = None
        last_err = ""
        for _ in range(12):
            try:
                deploy_id = self.trigger(**{k: v for k, v in kw.items()
                                            if k in ("deploy_type", "project_type",
                                                     "terminal_type")})
                break
            except BuildError as e:
                if "UDC_DEPLOY_0002" not in str(e):
                    return BuildResult(ok=False, state="TRIGGER_FAILED",
                                       problems=[str(e)])
                last_err = str(e)
                time.sleep(30)
        if deploy_id is None:
            return BuildResult(ok=False, state="TRIGGER_FAILED",
                               problems=[last_err or "构建锁未释放（UDC_DEPLOY_0002 重试 12 次）"])
        return self.wait(deploy_id, baseline=baseline)


# ---------------------------------------------------------------- 构建证据
#: ★ 构建成功不能推断运行成功 —— 交付报告里必须带这句话
BUILD_SEMANTICS_NOTE = (
    "构建成功仅代表平台编译/部署通过，不代表微流程在业务场景下真实运行成功。"
    "运行验证需另行触发流程并观察业务数据。"
)


def attach_semantics(result: BuildResult) -> BuildResult:
    """给构建结果挂上语义声明（防止下游误读为运行成功）。"""
    result.detail = dict(result.detail or {})
    result.detail["semantics"] = BUILD_SEMANTICS_NOTE
    return result
