import com.seeyon.udc.api.EntityAppService;
import com.seeyon.udc.api.ApplicationManagerAppService;
import com.seeyon.udc.common.dto.EntityDto;
import com.seeyon.udc.common.dto.AttributeDto;
import com.seeyon.udc.common.dto.DeployNormalDto;
import com.seeyon.udc.common.dto.DeployParamDto;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;

import java.util.ArrayList;
import java.util.List;

/**
 * 静态契约验证（UDC）：建实体 + 发布应用。
 * 字段填法来自 @DtoAttribute（见 api-usage/udc.md）：
 *   EntityDto.capFirstName      ← 首字母大写实体名称
 *   EntityDto.unCapFirstName    ← 首字母小写实体名称
 *   EntityDto.fullName          ← 实体fullName
 *   EntityDto.dtoFullName       ← 实体对应的dto的fullName
 *   EntityDto.attributes        ← 实体属性列表
 *   DeployNormalDto.lockCompatibility      ← 兼容性锁定
 *   DeployNormalDto.generateLog            ← 是否生成日志
 *   DeployNormalDto.entityFullNameCondition ← 数据传输(预置数据实体)参数
 *
 * 关键：DeployNormalDto 里**没有 appId**，appId 走请求上下文；
 *      appId/deployType/projectType/terminalType 是返回的 DeployParamDto 里的。
 */
public class ProbeUdc {

    /** 建实体：返回新实体 ID */
    public Long createEntity(EntityAppService entityAppService) {
        EntityDto dto = new EntityDto();
        dto.setCapFirstName("ProbeOrder");
        dto.setUnCapFirstName("probeOrder");
        dto.setFullName("com.seeyon.probe.entity.ProbeOrder");
        dto.setDtoFullName("com.seeyon.probe.dto.ProbeOrderDto");

        List<AttributeDto> attrs = new ArrayList<>();
        AttributeDto attr = new AttributeDto();
        attr.setName("probeName");
        attrs.add(attr);
        dto.setAttributes(attrs);

        SingleResponse<Long> response =
                entityAppService.create(SingleRequest.from(dto));
        return response.getData().getContent();
    }

    /** 发布应用：返回发布参数（含 deployId / appId / deployType） */
    public DeployParamDto deploy(ApplicationManagerAppService appManagerAppService) {
        DeployNormalDto dto = new DeployNormalDto();
        dto.setLockCompatibility(false);
        dto.setGenerateLog(true);

        SingleResponse<DeployParamDto> response =
                appManagerAppService.deployNormal(SingleRequest.from(dto));
        return response.getData().getContent();
    }
}
