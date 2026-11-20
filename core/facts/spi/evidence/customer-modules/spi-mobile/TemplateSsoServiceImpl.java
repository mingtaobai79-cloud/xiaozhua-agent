package com.seeyon.extend.spi.sso;

import com.seeyon.boot.util.JsonUtils;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.cip.connector.api.sso.SsoService;
import com.seeyon.cip.connector.enums.SsoClientTypeEnum;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.validation.constraints.NotBlank;
import java.util.Map;

/**
 * @author wangl
 * @version 1.0
 * @description: 连接器单点登录SPI开发模板
 * @date 202Sl7/23 15:11
 */
@Slf4j
public class TemplateSsoServiceImpl implements SsoService {
    /**
     * 获取唯一标识,需要全英文
     * 需要保证名称唯一,名称+SsoServiceImpl  为当前类名称,以当前template为例，实现类名称为 TemplateSsoServiceImpl
     * @return 英文标识
     */
    @Override
    public String getName() {
        return "template";
    }

    /**
     * 获取中文名称
     * 需要保证名称唯一
     * @return 中文名称
     */
    @Override
    public String getTypeCaption() {
        return "xx认证";
    }

    /**
     * 单点登录(核心)(
     * @param url 外部想跳转到的地址或标识
     * @param json 页面传递的数据
     * @param userMap 用户信息map,
         * innerUserId: 内部用户ID
         * innerUserName: 内部用户名称
         * innerUserCODE: 内部用户编号
         * outerUser: 外部用户账户
         * outerUserId: 外部用户ID
         * innerUserLoginName: 内部用户登录名
         * innerUserEmail: 内部用户邮箱
         * innerUserPhone: 内部用户手机号
         * innerUserOfficeNumber: 内部用户办公电话
         * innerUserBankAccount: 内部用户银行账户
         * innerUserOrgId: 内部用户组织编号
     * @param clientType 跳转类型(pc,移动)
     * @param extendParams 扩展参数,调用方传递的参数
     * @return 生成的单点登录地址
     */
    @Override
    public String login(String url, String json, Map<String, Object> userMap, SsoClientTypeEnum clientType, Map<String, Object> extendParams) {
        CasSsoDto casSsoDto = JsonUtils.fromJson(json, CasSsoDto.class);
        if(StringUtils.isBlank(url)){
            url = casSsoDto.defaultJumpUrl;
        }
        return url;
    }

    /**
     * 校验前端保存是给的参数
     * @param s 页面传递的数据
     */
    @Override
    public void check(String s) {
    }

    /**
     * 获取前端设计页面
     * @return 前端设计页面
     */
    @Override
    public String getPageJson() {
        return "{\"caption\":\"标准认证-CAS\",\"type\":\"cas\",\"extensionProperties\":[{\"colProps\":{\"span\":12},\"componentType\":\"Input\",\"componentProps\":{\"placeholder\":\"请输入\"},\"validateFirst\":true,\"rules\":[{\"required\":true,\"message\":\"请输入跳转地址\"},{\"pattern\":\"^[^\\\\s]*$\",\"message\":\"禁止输入空格\"},{\"type\":\"string\",\"max\":255,\"message\":\"最多255个字符\"}],\"caption\":\"跳转地址\",\"defaultValue\":\"\",\"name\":\"defaultJumpUrl\"}]}";
    }

    /**
     * 获取排序号
     * @return
     */
    @Override
    public Integer getSortNo() {
        return 99;
    }

    /**
     * 是否需要用户绑定操作,返回true时 login接口中的userMap才会有数据
     * @return true/false
     */
    @Override
    public boolean needUserBind() {
        return false;
    }

    @Getter
    @Setter
    public static class CasSsoDto {
        //跳转地址
        @NotBlank
        private String defaultJumpUrl;
    }
}
