/*
 * Decompiled with CFR 0.152.
 */
package com.seeyon.ctp.user.api.menu;

import com.seeyon.ctp.user.dto.menu.CtpUserThirdNavFrontDto;
import com.seeyon.ctp.user.dto.menu.ThirdMenuParamDto;
import com.seeyon.ctp.user.enums.MenuPositionEnum;
import java.util.List;

public abstract class AbstractThirdMenuService {
    public MenuPositionEnum position() {
        return MenuPositionEnum.TAIL;
    }

    public abstract List<CtpUserThirdNavFrontDto> selectThirdMenu(ThirdMenuParamDto var1);
}

