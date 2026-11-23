# ctp-message-facade + boot-starter-mq：发消息与消息队列

## Capability

**两件不同的事，别混：**
①`ctp-message-facade` = 平台消息中心（站内消息/在线状态/消息类型登记，含 **UDC 专用发消息接口**）；
②`boot-starter-mq` = 底层消息队列（Kafka / Redis / RocketMQ / SPI 四种实现按配置切换，`MessageProducer` 统一入口）。

## Version

`ctp-message-facade` 5.3.287 / `boot-starter-mq` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

无。MQ 走平台配置（`MQProperties`），4 种实现由配置选中，客开代码只依赖接口。

## ★ 一、给用户发消息（客开最常用）

```java
import com.seeyon.ctp.message.api.CtpUdcMessageSendAppService;
import com.seeyon.ctp.message.dto.UdcMessageSendUserDto;
import com.seeyon.boot.transport.SingleRequest;

@Autowired(required = false) private CtpUdcMessageSendAppService messageSend;

UdcMessageSendUserDto dto = new UdcMessageSendUserDto();
dto.setReceiveList(List.of(userId));                 // 接收人 id 列表
SingleResponse<String> r = messageSend.sendMessageByUser(SingleRequest.from(dto));
String msgId = r.getData().getContent();
```

```java
// 两个方法（字节码原文），都返回 SingleResponse<String>（消息 id）
SingleResponse<String> sendMessageByUser(SingleRequest<UdcMessageSendUserDto>);
SingleResponse<String> sendMessageByChooseJson(SingleRequest<UdcMessageSendChooseDto>);
```

DTO 极简：

```java
class UdcMessageSendUserDto   { List<Long> receiveList; }   // 收件人
class UdcMessageSendChooseDto { String chooseJson; }        // 前端选择器给的 JSON
```

⇒ 这是 **UDC/微流程场景的入口**；`CtpMessageSendAppService` 是标品内部面，客开不要用。

## 二、消息中心管理面（标品内部）

```java
CtpMessageManageAppService
  SingleResponse<Map<String,Boolean>> onlineInfo(SingleRequest<Long>)
  SingleResponse<Integer>  kickOffline(SingleRequest<KickOfflineDto>)
  SingleResponse<CtpMessageManageDto> selectBySetType(SingleRequest<Map<String,Object>>)
  SingleResponse<Map<ManageSetTypeEnum,String>> selectListByUserId(SingleRequest<Long>)
  SingleResponse<Integer>  set(SingleRequest<CtpMessageManageDto>)
  SingleResponse<Long>     onlineNumber()
  SingleResponse<Boolean>  deleteMessageRegister(SingleRequest<String>)
  SingleResponse<Integer>  getMessageNumber(SingleRequest<MessageStatusDto>)

CtpMessageOperateAppService
  SingleResponse<Integer> deleteMessageByIdentification(SingleRequest<String>)

CtpMessageSourceTypeAppService
  SingleResponse<Long> createSource(SingleRequest<CtpMessageSourceBaseDto>)
  SingleResponse<Long> createType(SingleRequest<CtpMessageTypeDto>)
```

## ★ 三、发 MQ 消息

```java
// 统一入口（接口，注入即可）：MessageProducer
String             send(BaseMessage msg);                 // 返回 msgId
List<String>       send(List<BaseMessage> msgs);          // 批量
boolean            sendDirectOneTime(BaseMessage msg);
String             sendDirectOneTimeReMsgId(BaseMessage msg);
boolean            isAvailable();

// AdvancedMessageProducer（extends 上面）
boolean send(MessageDto dto);
boolean sendBatch(List<MessageDto> dtos);
boolean sendDirectOneTime(MessageDto dto);
```

实现类（按平台配置选一个，客开不 new）：

```
KafkaProducerImpl / RedisProducerImpl / RocketMQProducerImpl / SpiMQProducerImpl
（均 extends AbstractMessageProducer implements AdvancedMessageProducer）
```

`MessageDto` 字段（字节码原文，16 个 —— 发消息前必须填对 4 个）：

```java
String fromApp;                 // ★ 来源应用
String topic;                   // ★ 主题（消费端按它匹配）
Long   tenantId;                // ★ 租户（跨租户必须显式给）
Object data;                    // ★ 载荷
String dataFullName;            //   载荷类全名（反序列化要用）
String msgId; Integer partition; Long executeTime;     // 延迟消息用 executeTime
Integer secretLevel; String grayTag; String traceId;
String createTime→createTime(Long); Map<String,String> customPassThrough;
TransferRequestContext transferRequestContext;
```

领域消息样例：`com.seeyon.ctp.message.info.MessageSend extends BaseMessage<MessageSendDto>`
（标品的「发消息」本身也是走 MQ 的）。

## 四、消费 MQ

```java
@MessageListener(topic = "my.topic", broadcast = false)   // 注解只有两个属性
public class MyConsumer extends AbstractMessageListener { ... }
```

消费实现：`MessageListenerImpl / MessageListenerService / KafkaConsumerImpl / RedisConsumerImpl /
RocketMQConsumerImpl / SpiMQConsumerImpl`；`AbstractMessageConsumer` 是共同基类。

常量：`MqConstant.CTP_MQ_SUBSCRIBE_KEY`、`MqConstant.ignoreLogTopic`。

## Side Effects

- `send` 返回 msgId 但**不代表已投递**（生产者有重投/恢复任务 `MessageRecoveryJob`）。
- 消息体落 `MQMessage` 表（`com.seeyon.boot.starter.mq.support.entity.MQMessage`），量大时注意清理。
- `kickOffline` 会真的把在线会话踢掉。

## Known Constraints

1. `CtpUdcMessageSendAppService` 两个方法都只包 `SingleRequest`，返回 `SingleResponse<String>`；**没有** 批量收件人以外的高级参数。
2. 客开不要直接 new `MessageDto` 后自己找 producer 实现类——注入接口 `MessageProducer`（Spring 按配置装配）。
3. `data` 是 `Object`，消费端靠 `dataFullName` 反序列化；
   改包名/改类名而不同步 `dataFullName` = 消费端拿不到对象。
4. 延迟消息用 `executeTime`（毫秒时间戳），不是 `DelayMessageDto` 的 tag 字符串。
5. 本格全部来自字节码契约，**未真机发过消息**（UNVERIFIED：真实 topic/dispatch 行为）。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `CtpUdcMessageSendAppService` 2 方法 | `javap -p` 5.3.287 原文 | VERIFIED_STATIC_BYTECODE |
| `UdcMessageSendUserDto` 仅 1 字段 `receiveList` | 同上 | VERIFIED_STATIC_BYTECODE |
| `CtpMessageManageAppService` 8 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `MessageProducer` 6 方法 + 4 实现 | `javap -p` 5.3.600 原文 | VERIFIED_STATIC_BYTECODE |
| `MessageDto` 16 字段 | 同上 | VERIFIED_STATIC_BYTECODE |
| `@MessageListener` 2 属性 | 同上 | VERIFIED_STATIC_BYTECODE |
| `MessageSend extends BaseMessage<MessageSendDto>` | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部方法名/字段名可逐字复核（jar 在盘）
- ⚠️ 没有真机调用记录：发消息、MQ 收发均未跑（缺 topic 与目标用户样本）

## 给 Agent 的判据

```
微流程/客开要通知用户        → CtpUdcMessageSendAppService.sendMessageByUser(SingleRequest<UdcMessageSendUserDto>{receiveList})
要给别的模块发异步事件        → MessageProducer.send(BaseMessage) 或 AdvancedMessageProducer.send(MessageDto)
要收异步事件                 → @MessageListener(topic=...) + extends AbstractMessageListener
消息没发出去                  → 先看 producer.isAvailable()，再看 fromApp/topic/tenantId 三件
延迟投递                      → MessageDto.executeTime = System.currentTimeMillis()+delay
```
