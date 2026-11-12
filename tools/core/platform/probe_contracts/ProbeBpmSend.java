import com.seeyon.bpm.api.common.BpmAppService;
import com.seeyon.bpm.dto.operation.openapi.BpmSendDto;
import com.seeyon.bpm.dto.operation.openapi.BpmSendResultDto;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;

/**
 * 静态契约验证：只用真实 jar 编译，不运行。
 * 编译通过 = 接口全名 / 方法名 / DTO 字段名 / 字段类型 / 取值链 全对。
 *
 * 字段填法全部来自 @DtoAttribute 的说明（见 api-usage/bpm.md）：
 *   templateCode  ← 模板code
 *   templateId    ← 模板ID · 模板code/模板ID两者传其一，如果都传，以模板code为准
 *   currentUserId ← userCode · 例:1 · 关联 OrgMemberDto
 *   orgId         ← orgCode · 例:1 · 关联 OrgUnitDto
 *   formRecordId  ← 表单数据id
 *   caseId        ← 流程实例ID
 *   sendPolicy    ← 流程发送策略，现有：添加节点 - node ; 抛异常 - exception
 */
public class ProbeBpmSend {

    public BpmSendResultDto send(BpmAppService bpmAppService) {
        BpmSendDto dto = new BpmSendDto();

        // 按 @DtoAttribute：模板 code 与 ID 传其一，都传以 code 为准 → 只传 code
        dto.setTemplateCode("PROBE_TEMPLATE_001");

        // currentUserId 的 value 是 userCode，relationDto 指向 OrgMemberDto
        dto.setCurrentUserId(1L);
        dto.setOrgId(1L);

        dto.setFormRecordId("PROBE_FORM_RECORD_001");
        dto.setSendPolicy("node");

        SingleResponse<BpmSendResultDto> response =
                bpmAppService.send(SingleRequest.from(dto));

        // 取值链固定：getData() → getContent()
        return response.getData().getContent();
    }
}
