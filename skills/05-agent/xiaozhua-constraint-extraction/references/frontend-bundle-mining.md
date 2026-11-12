# 前端 bundle 挖掘：设计器值域与 GraphQL 面

适用：需要 UDC（或 BPM/ORG/USER）**设计态值域、类型全集、默认模板、控件映射**，或判断某个前端 op 走 REST 还是 GraphQL。

## 1. chunk 布局
解包目录形如 `.../udc-frontend/unpacked/`；每个子目录名 ≈ 原源码路径 + hash（如 `src_redux_store_ts.<hash>/`、`src_components_design_settings_.../`），内含 `module-<id>.js`。这些是 webpack chunk，ESM 语法（`export let`）+ 内联 `require(<id>)`。

## 2. 抽取（权威表 → JSON）
用 `scripts/extract_chunk_tables.mjs`。要点：
- 必须注入 `require` stub（`new Proxy`），否则带 require 的 chunk 动态 import 会抛 `ReferenceError: require is not defined in ES module scope`
- 写临时 `.mjs` 再 `await import('file:///...mjs?t=' + Date.now())`（`?t=` 破缓存）
- 收集导出：`[...src.matchAll(/export let ([A-Za-z_$0-9]+)/g)]`
- `Map` 导出要 `Object.fromEntries` 才能 JSON 化
- 表键常用计算属性 `[pe.String]`：求值后自然还原为 `"STRING"`

## 3. UDC 属性 dataType（实测，前端设计器为准）
| 表 | 内容 | 数量 |
|---|---|---|
| 类型注册表（`pe`） | JavaType→dataType，**值域全集** | 34 |
| 中文名（`d4`） | dataType→中文名 | 34（另一 chunk 23） |
| 默认模板（`Uz`） | dataType→默认属性（maxLength/min/max/decimalDigits/multiSelect/relationType…） | 14 |
| 值域（`WB`） | 长度/数值 min-max | 6 |
| 日期格式（`fU`） | DATETIME/DATE/TIME | 3 |
| 控件映射（`py`） | dataType→PC/移动端控件 | 19 |
| 可新建白名单（`mG`） | 新建字段下拉项 | 9 |

- **值域 34 种**：STRING INTEGER FLOAT DOUBLE LONG BIGINTEGER DECIMAL BOOLEAN DATE DATETIME TIME ENTITY OBJECT DTO CTPENUM ENUM ATTACHMENT CURRENCY MULTILINESTRING IMAGE ARRAY SELECTPEOPLE Serial CONTENT OPINIONHANDLER MAP ORGGROUP ASSOCIATEDOCUMENT METADATA DATA_SOURCE DOCUMENTNUMBER OPINION ELEMENT PERSONSELECTOR
- **可新建 9 种**：STRING INTEGER BIGINTEGER DECIMAL CURRENCY DATE TIME DATETIME BOOLEAN
- **值域 `WB`**：STRING 0–4000、MULTILINESTRING 0–10000、INTEGER ±2147483647、BIGINTEGER/DECIMAL/CURRENCY ±9007199254740991
- **默认模板样例**：STRING maxLength 50、MULTILINESTRING 300、DECIMAL decimalDigits 2、ATTACHMENT multiSelect true、BOOLEAN defaultValue `"true"`、ENUM/CTPENUM/ENTITY relationType `Many2OneAssociation`
- **后端对证**：`boot-starter-datatype` 只有 15 个运行时类型（STRING MULTILINESTRING INTEGER BIGINTEGER DECIMAL BOOLEAN DATE DATETIME TIME ENUM ENTITY ATTACHMENT ARRAY，Double 的 name 也复用 DECIMAL），caption 走 i18n key `com.seeyon.boot.enums.DataType.<NAME>` → **是设计态值域的子集**
- 由默认模板反推「类型-属性矩阵」：有 minLength/maxLength 的只有 STRING/MULTILINESTRING；有 decimalDigits 的只有 DECIMAL/CURRENCY；有 multiSelect 的只有 ENUM/CTPENUM/ENTITY/ATTACHMENT；引用型需 relationType。校验器据此报「不支持属性 X」。

## 4. op 通道判定（REST vs GraphQL）
- REST 对不上就试 GraphQL：`grep -nE '@(Post|Get)Mapping' udc-web/com/seeyon/udc/controller/*.java`
- GraphQL loader 用法特征：
  ```js
  a.wh.udcQueryLoader.load({ fieldType:"udcMicroflowFindNodesGet",
      paramsType:"udcMicroflowFindNodesGetInputQuery", paramsKey:"query",
      queryFields:"\n content{ caption type actionType tag icon order paramDefinitionSchema }\n ",
      params:{ nodeGroupEnum } });
  a.wh.udcMutationLoader.load({ fieldType:"udcAffairListPost",
      paramsType:"udcAffairListPostInputBody", paramsKey:"body", params:{...} });
  ```
  `Get` 后缀→query，`Post` 后缀→mutation；`paramsKey` ∈ {`query`,`body`}=GraphQL 变量名
- **内省不可用**：生产 `__schema{queryType{fields}}` 返回 0 字段（被禁）；不要据此判「字段不存在」，以 chunk 内 loader 定义为准
- 命名规则仍适用：`udc<Base><Path Pascal><Get|Post>`；op 名由前端 loader 的 `fieldType` 明确给出
