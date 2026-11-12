/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.EnumInfo
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.bpm.enums;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.EnumInfo;
import com.seeyon.boot.enums.Messageable;

@EnumInfo(value="\u6d41\u7a0b\u4fee\u6539\u7c7b\u578b", customs={@Custom(properties={@CustomAttribute(name="appName", value="bpm")})}, excludes={"NONE"})
public enum ChangeTypeEnum implements Messageable
{
    NONE(-1),
    AddNode(0),
    AddInform(1),
    Assign(2),
    DeleteNode(3),
    PassRead(4),
    Transfer(5),
    OrderExecuteAdd(6),
    ReplaceNode(7),
    ModifyNodeProperty(8),
    Countersign(9),
    LOOP(10),
    SuperviseChange(11),
    CountersignInnerAdd(12),
    PostApprovalAddNode(13),
    ADD_INNER(14);

    private int code;

    private ChangeTypeEnum(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}
