# 表达式函数用法目录（88 个 / 8 组）

> 证据等级：**LIVE**（`POST /service/udc/expression/preset/list`，
> test2 2026-10-23，`terminalSupportType=BACKEND`）
> 生成器：`tools/core/expression/gen_function_catalog.py`（勿手改本文件，改生成器）
>
> ⚠ `BACKEND` 88 个；`FRONTEND` 只要 81 个（缺「变化函数」「枚举函数」两组，
> 且「基础函数」从 15 降到 11）。见 `terminal.py`。
>
> 用法：函数 token 的 `value` 用下表 `函数名`，`subOps` 按参数顺序给二维数组；
> 参数是变量时必须带 `uniformityParams.paramId`。

## 总览

| 分组 | 数量 | 函数 |
|---|---|---|
| 基础函数 | 15 | isNull、multMemberBelongsTo、isNotNull、multUnitBelongsTo、contains、notContains、containsAny、notContainsAny、memberBelongsTo、thereIn、idGenerate、unitBelongsTo、uniqueMark、rand、randBetween |
| 日期函数 | 24 | dateToString、stringToDate、dateDiff、minuteDiff、hoursDiff、timeMinuteDiff、timeDiff、year、month、day、addDay、addMon、addHourToTime、addHour、addMinuteToTime、addMinutes、getWeekday、getHours、getMinutes、getSeconds、getHoursByTime、getMinutesByTime、getSecondsByTime、getTimeStampByDate |
| 数学函数 | 10 | roundOff、roundOffCeiling、roundOffFloor、quotient、thousandBitSep、textToInt、textToLong、textToDecimal、abs、round |
| 文本函数 | 17 | startsWith、notStartsWith、endsWith、notEndsWith、containsText、split、join、indexOf、len、substringByIndex、replace、find、substring、subStituteAll、subStitute、rmbUpperCase、rmbUpperForShort |
| 条件函数 | 1 | ifs |
| 聚合函数 | 18 | sum、count、avg、min、max、sumif、countIf、avgif、allLineMatch、anyLineMatch、getListIndex、getSubValueByEarliest、getSubValueByLatest、getSubValueByMaxIf、getSubValueByMinIf、getSubValueByEarliestIf、getSubValueByLatestIf、listUnique |
| 变化函数 | 1 | changeTo |
| 枚举函数 | 2 | getEnumItemName、getEnumItemValue |

---

## 基础函数（15）

### `isNull` — 为空

参数：`对象`

说明：判断文本或属性是否为空

示例：`isNull(扣缴义务人)`　参数类型：对象

→ 判定扣缴义务人是否为空

### `multMemberBelongsTo` — 多维组织人员隶属

参数：`人员参数 / 被判断值`

### `isNotNull` — 不为空

参数：`对象`

说明：判断文本或属性是否不为空

示例：`isNotNull(扣缴义务人)`　参数类型：对象

→ 判定扣缴义务人不为空

### `multUnitBelongsTo` — 多维组织隶属

参数：`组织参数 / 被判断值`

### `contains` — 包含(全部)

参数：`参数 / 被包含变量`

说明：判断一个字段是否包含全部指定的值，支持多个值判断，满足全部才返回true，且判断结果与值顺序无关

示例：`contains(候选人, {张三，李四})`　参数类型：对象 / 对象

→ 候选人为{张三，李四，王五}，候选人中既有张三，也有李四，返回true

### `notContains` — 不包含(全部)

参数：`参数 / 被包含变量`

说明：判断参数是否所有值均不在字段中，若是，则返回true，否则返回false，且判断结果与值顺序无关

示例：`notContains(候选人, {张三，李四})`　参数类型：对象 / 对象

→ 候选人为{李四，王五}，候选人没有张三和李四，即没有包含右值中的全部人，返回true

### `containsAny` — 包含任一

参数：`参数 / 被包含变量`

说明：判断一个字段是否包含指定的值，支持多个值判断，满足其一即返回true，且判断结果与值顺序无关

示例：`containsAny(候选人, {张三，李四})`　参数类型：对象 / 对象

→ 候选人为{李四，王五，胡六}，候选人包含张三或李四中任意一人，则返回true

### `notContainsAny` — 不包含任一

参数：`参数 / 被包含变量`

说明：判断一个字段是否不包含指定值中的任意一个，若是，则返回true，否则返回false，且判断结果与值顺序无关

示例：`notContainsAny(候选人, {张三，李四})`　参数类型：对象 / 对象

→ 候选人为{王五，胡六}，候选人中没有张三和李四中的任意一个，返回true

### `memberBelongsTo` — 人员隶属

参数：`人员参数 / 被判断值`

示例：`memberBelongsTo(张三, 北京分部;开发岗位;P1;开发经理)`　参数类型：对象 / 对象

→ 张三 是否隶属于 北京分部（组织）;开发岗位（岗位）;P1（职级）;开发经理（职务）

### `thereIn` — 属于

参数：`参数1 / 参数2`

说明：判断参数1集合是否完全属于参数2集合，或者文本1是否属于文本2

示例：`thereIn(张三;李四, 张三;王五;李四)`　参数类型：对象 / 对象

→ 返回为true

### `idGenerate` — ID生成

参数：无

说明：返回长整数类型的ID标识

示例：`idGenerate()`

→ 生成长整数类型的ID标识

### `unitBelongsTo` — 组织隶属

参数：`组织参数 / 被判断值`

示例：`unitBelongsTo(北京分部, 集团)`　参数类型：对象 / 对象

→ 北京分部 是否隶属于 集团（含下级）

### `uniqueMark` — 唯一标识

参数：无

说明：返回唯一标识字符串

示例：`uniqueMark()`

→ 生成长度为32位的唯一标识

### `rand` — 随机数

参数：无

说明：返回一个大于等于0且小于1的随机实数

### `randBetween` — 指定范围随机数

参数：`最小整数 / 最大整数`

说明：返回位于两个指定数之间的一个随机整数

## 日期函数（24）

### `dateToString` — 日期转文本

参数：`日期 / 格式`

示例：`dateToString(申请日期, yyyy-MM-dd)`　参数类型：日期 / 文本

→ 将申请日期转为yyyy-MM-dd的日期字符串(如: 2021-01-01)

### `stringToDate` — 文本转日期

参数：`日期字符串 / 日期格式`

示例：`stringToDate(2021-01-01, yyyy-MM-dd)`　参数类型：文本 / 文本

→ 将日期字符串按格式yyyy-MM-dd转为日期类型

### `dateDiff` — 日期天数差

参数：`日期1 / 日期2`

示例：`dateDiff(开始日期时间, 结束日期时间)`　参数类型：日期 / 日期

→ 开始日期时间和结束日期时间的天数差

### `minuteDiff` — 日期分钟差

参数：`日期1 / 日期2`

示例：`minuteDiff(开始日期时间, 结束日期时间)`　参数类型：日期 / 日期

→ 开始日期时间和结束日期时间的分钟差

### `hoursDiff` — 日期小时差

参数：`日期1 / 日期2`

示例：`hoursDiff(开始日期时间, 结束日期时间)`　参数类型：日期 / 日期

→ 开始日期时间和结束日期时间的小时差

### `timeMinuteDiff` — 时间分钟差

参数：`时间1 / 时间2`

示例：`timeMinuteDiff(12:00:00, 12:10:00)`　参数类型：文本 / 文本

→ 对比两个时间类型的分钟差, 这里返回10

### `timeDiff` — 时间比较

参数：`时间1 / 时间2`

说明：比较两个时间类型字段的大小，若前者大于后者，则返回true，否则返回false

### `year` — 获取指定日期的年份

参数：`日期`

说明：获取指定日期的年

示例：`year(审核日期)`　参数类型：日期

→ 获取审核日期的年份

### `month` — 获取指定日期的月份

参数：`日期`

说明：获取指定日期的月，返回值是介于 1 到 12 之间的整数。

示例：`month(审核日期)`　参数类型：日期

→ 获取审核日期的月份

### `day` — 获取指定日期的天数

参数：`日期`

说明：获取指定日期的天，返回值是介于 1 到 31 之间的整数。

示例：`day(审核日期)`　参数类型：日期

→ 获取审核日期的日期天数

### `addDay` — 增加天数

参数：`日期或日期时间 / 天数`

示例：`addDay(申请日期, 2)`　参数类型：日期 / 对象

→ 将申请日期增加2天

### `addMon` — 增加月数

参数：`日期或日期时间 / 月数`

说明：增加日期或日期时间字段的月数

示例：`addMon(2024-11-30, 3)`　参数类型：日期 / 对象

→ 返回 2025-02-28

### `addHourToTime` — 增加小时(时间)

参数：`时间 / 小时数`

示例：`addHourToTime(12:00:01, 2)`　参数类型：文本 / 对象

→ =14:00:01

### `addHour` — 增加小时

参数：`日期或日期时间 / 小时数`

示例：`addHour(申请日期, 2)`　参数类型：日期 / 对象

→ 将申请日期增加2个小时

### `addMinuteToTime` — 增加分钟(时间)

参数：`时间 / 分钟数`

示例：`addMinuteToTime(12:00:00, 30)`　参数类型：文本 / 对象

→ =12:30:00

### `addMinutes` — 增加分钟

参数：`日期或日期时间 / 分钟数`

示例：`addMinutes(申请日期, 30)`　参数类型：日期 / 对象

→ 将申请日期增加30分钟

### `getWeekday` — 获取星期几

参数：`日期或日期时间`

说明：返回指定日期对应的星期几

示例：`getWeekday(2022-05-13)`　参数类型：日期

→ 返回"星期五"

### `getHours` — 获取指定日期的小时数

参数：`日期或日期时间`

示例：`getHours(2022-05-21 12:04:09)`　参数类型：日期

→ 返回 12

### `getMinutes` — 获取指定日期的分钟数

参数：`日期或日期时间`

示例：`getMinutes(2022-05-21 12:04:09)`　参数类型：日期

→ 返回 4

### `getSeconds` — 获取指定日期的秒数

参数：`日期或日期时间`

示例：`getSeconds(2022-05-21 12:04:09)`　参数类型：日期

→ 返回 9

### `getHoursByTime` — 获取指定时间的小时数

参数：`时间`

示例：`getHoursByTime(12:04:09)`　参数类型：文本

→ 返回 12

### `getMinutesByTime` — 获取指定时间的分钟数

参数：`时间`

示例：`getMinutesByTime(12:04:09)`　参数类型：文本

→ 返回 4

### `getSecondsByTime` — 获取指定时间的秒数

参数：`时间`

示例：`getSecondsByTime(12:04:09)`　参数类型：文本

→ 返回 9

### `getTimeStampByDate` — 获取指定日期的时间戳

参数：`日期或日期时间`

示例：`getTimeStampByDate(申请日期)`　参数类型：日期

→ 返回1653381754415

## 数学函数（10）

### `roundOff` — 取整

参数：`数字`

说明：四舍五入取整

示例：`roundOff(数字)`　参数类型：对象

→ 四舍五入保留数字的整数位

### `roundOffCeiling` — 向上取整

参数：`数字`

示例：`roundOffCeiling(数字)`　参数类型：对象

→ 向上取整(1.2) 返回2 

### `roundOffFloor` — 向下取整

参数：`数字`

示例：`roundOffFloor(数字)`　参数类型：对象

→ 向下取整(1.9) 返回1 

### `quotient` — 取商

参数：`被除数 / 除数`

示例：`quotient(被除数, 除数)`　参数类型：对象 / 对象

→ 取商(7,2) 返回3 

### `thousandBitSep` — 千分位显示

参数：`待转换字段`

说明：返回千位分隔符转换后格式

示例：`thousandBitSep(10000)`　参数类型：对象

→ 输出 10,000

### `textToInt` — 文本转整数

参数：`文本`

示例：`textToInt(10000)`　参数类型：文本

→ 将文本10000转为整数10000

### `textToLong` — 文本转长整数

参数：`文本`

示例：`textToLong(9007199254740990)`　参数类型：文本

→ 将文本9007199254740990转为长整数9007199254740990

### `textToDecimal` — 文本转小数

参数：`文本`

示例：`textToDecimal(100.76)`　参数类型：文本

→ 将文本100.76转为小数100.76

### `abs` — 绝对值

参数：`数字`

说明：返回参数的非负值

示例：`abs(-1)`　参数类型：对象

→ 返回1

### `round` — 四舍五入

参数：`数值：小数、货币、整数、长整数 / 位数：0-10`

说明：将数字四舍五入到指定的位数

示例：`round(3.14159, 3)`　参数类型：对象 / 整数

→ 返回3.142

## 文本函数（17）

### `startsWith` — 开头为

参数：`字符串 / 开头字符串`

示例：`startsWith(字符串1, 字符串2)`　参数类型：对象 / 对象

→ 字符串1是否以字符串2开头

### `notStartsWith` — 开头不为

参数：`字符串 / 开头字符串`

示例：`notStartsWith(字符串1, 字符串2)`　参数类型：对象 / 对象

→ 字符串1是否不以字符串2开头

### `endsWith` — 结尾为

参数：`字符串 / 结尾字符串`

示例：`endsWith(字符串1, 字符串2)`　参数类型：文本 / 文本

→ 字符串1是否以字符串2结尾

### `notEndsWith` — 结尾不为

参数：`字符串 / 结尾字符串`

示例：`notEndsWith(字符串1, 字符串2)`　参数类型：文本 / 文本

→ 字符串1是否不以字符串2结尾

### `containsText` — 文本包含

参数：`参数 / 被包含文本`

说明：判断文本是否包含另一段文本

示例：`containsText(字符串1, 字符串2)`　参数类型：对象 / 对象

→ 判断字符串1是否包含字符串2

### `split` — 按指定符号分割文本

参数：`指定文本 / 指定符号`

示例：`split(张三;李四;王五, ;)`　参数类型：文本 / 文本

→ 将文本"张三;李四;王五"按符号";"分隔为文本数组["张三" , "李四", "王五"]

### `join` — 按指定符号合并文本数组

参数：`文本数组 / 指定符号`

示例：`join(文本数组, ;)`　参数类型：集合 / 文本

→ 将文本数组以 ; 合并

### `indexOf` — 获取指定下标文本

参数：`文本数组 / 指定下标`

说明：获取文本数组指定下标文本

示例：`indexOf(文本数组, 1)`　参数类型：对象 / 整数

→ 获取文本数组下标1的文本

### `len` — 获取字符串长度

参数：`字符串`

示例：`len(张三)`　参数类型：文本

→ =2

### `substringByIndex` — 按位置截取字符串

参数：`字符串 / 起始位置 / 结束位置`

示例：`substringByIndex(我的名字是张三, 3, 4)`　参数类型：文本 / 整数 / 整数

→ =名字

### `replace` — 按位置替换字符串

参数：`要替换的字符串 / 开始替换的位置 / 从开始位置替换的字符个数 / 新的替换文本`

示例：`replace(happy birthday, 7, 9, new year)`　参数类型：文本 / 整数 / 整数 / 对象

→ 输出: happy new year

### `find` — 查找文本位置

参数：`查找文本 / 被查找文本 / 查找起始位置`

示例：`find(张三丰, 张三, 1)`　参数类型：文本 / 文本 / 整数

→ =1

### `substring` — 按长度截取字符串

参数：`字符串 / 起始位置 / 截取长度`

示例：`substring(我的名字是张三, 3, 2)`　参数类型：文本 / 整数 / 整数

→ =名字

### `subStituteAll` — 按内容替换字符串

参数：`要替换的字符串 / 被替换文本 / 新的替换文本`

示例：`subStituteAll(2011年第一度, 1, 2)`　参数类型：文本 / 对象 / 对象

→ 输出: 2022年第一季度

### `subStitute` — 按内容位置替换字符串

参数：`要替换的字符串 / 被替换文本 / 新的替换文本 / 匹配第几个位置`

示例：`subStitute(2011年第一度, 1, 2, 2)`　参数类型：文本 / 对象 / 对象 / 整数

→ 输出: 2012年第一季度

### `rmbUpperCase` — 人民币大写

参数：`数字`

说明：数值类型转换为人民币大写

示例：`rmbUpperCase(120.52)`　参数类型：对象

→ 返回: 壹佰贰拾元伍角贰分

### `rmbUpperForShort` — 人民币小写

参数：`数值`

说明：数值类型转换为人民币小写

示例：`rmbUpperForShort(120.52)`　参数类型：对象

→ 返回: 一百二十元五角二分

## 条件函数（1）

### `ifs` — 条件返回

参数：`条件 / 结果1 / 结果2`

说明：按条件返回对应结果

示例：`ifs(条件, 结果1, 结果2)`　参数类型： / 对象 / 对象

→ 如果满足条件返回结果1，否则返回结果2

## 聚合函数（18）

### `sum` — 明细表求和

参数：`明细表属性`

示例：`sum(订单表.订单明细表.金额)`　参数类型：对象

→ 求对订单明细表金额求和

### `count` — 明细表计数

参数：`明细表对象`

示例：`count(订单表.订单明细表)`　参数类型：集合

→ 求对订单明细表的记录数

### `avg` — 明细表求平均

参数：`明细表属性`

示例：`avg(订单表.订单明细表.金额)`　参数类型：对象

→ 求对订单明细表金额求平均

### `min` — 明细表求最小值

参数：`明细表属性`

示例：`min(订单表.订单明细表.金额)`　参数类型：对象

→ 求对订单明细表金额求最小值

### `max` — 明细表求最大值

参数：`明细表属性`

示例：`max(订单表.订单明细表.金额)`　参数类型：对象

→ 求对订单明细表金额求最大值

### `sumif` — 明细表条件求和

参数：`条件 / 求和属性`

示例：`sumif(订单.订单明细表.金额 > 100, 订单.订单明细表.金额)`　参数类型：对象 / 文本

→ 
            对订单明细表中金额大于100的记录金额求和
        

### `countIf` — 明细表条件计数

参数：`条件`

示例：`countIf(订单.订单明细表.金额 > 100)`　参数类型：对象

→ 
            返回满足条件 金额 > 100 的记录数
        

### `avgif` — 明细表条件求平均

参数：`条件 / 求平均字段属性`

示例：`avgif(订单.订单明细表.金额 > 100, 订单.订单明细表.金额)`　参数类型：对象 / 文本

→ 
            对订单明细表中金额大于100的记录金额求平均
        

### `allLineMatch` — 明细表所有行满足

参数：`条件`

示例：`allLineMatch(订单明细表.金额 > 100)`　参数类型：对象

→ 
            订单明细表是否满足所有订单记录的订单金额大于100
        

### `anyLineMatch` — 明细表任意行满足

参数：`条件`

示例：`anyLineMatch(订单明细表.金额 > 100)`　参数类型：对象

→ 
            订单明细表是否存在任意一条订单记录的订单金额大于100
        

### `getListIndex` — 获取明细行字段

参数：`待获取属性 / 用于定位明细行第几行`

示例：`getListIndex(明细子表.报销金额, 0)`　参数类型：对象 / 对象

→ 得到明细子表第一行的报销金额

### `getSubValueByEarliest` — 明细表最早行取值

参数：`明细表日期/日期时间字段 / 明细表取值字段`

说明：求明细表记录中日期/日期时间字段值最早的行，并返回该行指定字段的值

示例：`getSubValueByEarliest(订单明细表.创建时间, 订单明细表.订单名称)`　参数类型：对象 / 对象

→ 求订单明细表中创建时间最早的订单名称

### `getSubValueByLatest` — 明细表最晚行取值

参数：`明细表日期/日期时间字段 / 明细表取值字段`

说明：求明细表记录中日期/日期时间字段值最晚的行，并返回该行指定字段的值

示例：`getSubValueByLatest(订单明细表.创建时间, 订单明细表.订单名称)`　参数类型：对象 / 对象

→ 求订单明细表中创建时间最晚的订单名称

### `getSubValueByMaxIf` — 明细表条件求最大值

参数：`条件 / 明细表数字字段`

说明：求满足条件的明细表记录中，数值字段值最大的行，并返回对应的值

示例：`getSubValueByMaxIf(订单表.日期 = 系统日期, 订单表.金额)`　参数类型：对象 / 对象

→ 求当天，订单表中金额最大的明细项金额

### `getSubValueByMinIf` — 明细表条件求最小值

参数：`条件 / 明细表数值字段`

说明：求满足条件的明细表记录中，数值字段值最小的行，并返回对应的值

示例：`getSubValueByMinIf(订单表.日期 = 系统日期, 订单表.金额)`　参数类型：对象 / 对象

→ 求当天，订单明细表中金额最小的明细项金额

### `getSubValueByEarliestIf` — 明细表条件求最早值

参数：`条件 / 明细表日期/日期时间字段`

说明：求满足条件的明细表记录中，条件字段（日期/日期时间）值最早的行，并返回对应的值

示例：`getSubValueByEarliestIf(订单明细表.日期 = 系统日期, 订单明细表.创建时间)`　参数类型：对象 / 对象

→ 求当天，订单明细表中最早创建的明细项时间

### `getSubValueByLatestIf` — 明细表条件求最晚值

参数：`条件 / 明细表日期/日期时间字段`

说明：求满足条件的明细表记录中，条件字段（日期/日期时间）值最晚的行，并返回对应值

示例：`getSubValueByLatestIf(订单明细表.日期 = 系统日期, 订单明细表.创建时间)`　参数类型：对象 / 对象

→ 求当天，订单明细表中最晚创建的明细项时间

### `listUnique` — 明细表列不重

参数：`明细表属性`

说明：明细表某列字段值是否多行不重复, 仅适用于校验规则设置

## 变化函数（1）

### `changeTo` — 值变化

参数：`变化前的值 / 变化后的值 / 期望值`

说明：判断变量是否从旧值变为预期的新值

示例：`changeTo(订单状态(旧值), 订单状态(新值), 已支付)`　参数类型：对象 / 对象 / 对象

→ 订单状态变为已支付

## 枚举函数（2）

### `getEnumItemName` — 获取枚举项名称

参数：`枚举项id`

示例：`getEnumItemName(枚举变量)`　参数类型：长整数

→ 根据枚举项id获取枚举项的名称

### `getEnumItemValue` — 获取枚举项值

参数：`枚举项id`

示例：`getEnumItemValue(枚举变量)`　参数类型：长整数

→ 根据枚举项id获取枚举项的值
